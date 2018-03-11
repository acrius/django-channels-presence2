from time import mktime
from datetime import datetime
from collections import Iterable
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.functional import SimpleLazyObject

from .exceptions import PresenceError


class PresenceEvents:
	JOIN_USER = 'join.user'
	LEAVE_USER = 'leave.user'


class ChannelPresence:
	@classmethod
	async def create_from_consumer(cls, consumer, groups):
		return await cls.create(consumer.channel_layer, consumer.scope['user'], groups)

	@classmethod
	async def create(cls, channel_layer, user, groups):
		self = cls()

		if not user.is_anonymous:
			self.user = user
		else:
			raise PresenceError('To use presence, the user should not be anonymous.')

		self.channel_layer = channel_layer

		if isinstance(groups, Iterable):
			self.groups = groups
		else:
			raise PresenceError('Groups should be iterable of groups names.')

		self.expired_activity = getattr(settings, 'EXPIRED_USER_ACTIVITY', 60 * 5)
		self.rooms = set()

		return self

	async def join(self, rooms=None):
		await self.update_presence(rooms=rooms)
		await self.send(type=PresenceEvents.JOIN_USER, user_pk=self.user.pk, groups=list(self.groups),
						rooms=list(rooms or self.rooms))

	async def leave(self, rooms=None):
		await self.update_presence(leave=True, rooms=rooms)
		await self.send(type=PresenceEvents.LEAVE_USER, user_pk=self.user.pk, groups=list(self.groups),
						rooms=list(rooms or self.rooms))

	async def send(self, **event):
		for group in self.groups:
			await self.channel_layer.group_send(group, event)

	async def update_presence(self, leave=False, rooms=None):
		rooms = rooms or self.rooms

		locations = (
			*(self._presence_key(group) for group in self.groups),
			*(self._presence_key(group, room=room) for group in self.groups for room in rooms)
		)

		timestamp = self._from_date_to_int(datetime.now())

		pool = await self.channel_layer.connection(self.channel_layer.consistent_hash(self.groups[0]))
		with (await pool) as connection:
			for location in locations:
				await connection.zadd(location, (-1 if leave else 1) * timestamp, self.user.pk)

		if rooms:
			self.rooms = set(*self.rooms, *rooms)

	async def get_users(self, group, room=None):
		pool = await self.channel_layer.connection(self.channel_layer.consistent_hash(group))
		presence_key = self._presence_key(group, room=room)
		now_timestamp = self._from_date_to_int(datetime.now())
		with (await pool) as connection:
			return [{
				'user': await sync_to_async(self.get_lazy_user)(user_pk),
				'present_at': self._from_int_to_date(timestamp),
				'is_active': True if timestamp > 0 and now_timestamp - timestamp < self.expired_activity else False
			} for user_pk, timestamp in await connection.zrange(presence_key, start=0, stop=-1, withscores=True)]

	@staticmethod
	def get_lazy_user(user_pk):
		return SimpleLazyObject(lambda: get_user_model().objects.get(pk=user_pk))

	def _presence_key(self, group, room=None):
		assert self.channel_layer.valid_group_name(group), "Group name not valid"
		group_key = self._group_key(group)

		return '{}:{}:presence'.format(group_key, room) if room else '{}:presence'.format(group_key)

	def _group_key(self, group):
		return "{}:group:{}".format(self.channel_layer.prefix, group)

	@staticmethod
	def _from_int_to_date(date):
		return datetime.fromtimestamp(date)

	@staticmethod
	def _from_date_to_int(date):
		return int(mktime(date.timetuple()))
