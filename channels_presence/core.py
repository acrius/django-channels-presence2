from time import mktime
from datetime import datetime
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.functional import SimpleLazyObject

from .exceptions import PresenceError


class ChannelPresence:
	@classmethod
	async def create_from_consumer(cls, consumer):
		return await cls.create(consumer.channel_layer, consumer.scope['user'])

	@classmethod
	async def create(cls, channel_layer, user):
		self = cls()
		if not user.is_anonymous:
			self.user = user
		else:
			raise PresenceError('To use presence, the user should not be anonymous.')
		self.channel_layer = channel_layer
		self.expired_activity = settings.get('EXPIRED_USER_ACTIVITY', 60 * 5)

		return self

	async def join(self, group, room=None):
		self.update_presence(group, room=room)

	async def leave(self, group, room=None):
		self.update_presence(group, leave=True, room=room)

	async def update_presence(self, group, leave=False, room=None):
		locations = (
			self._presence_key(group),
			*((self._presence_key(group, room=room),) if room else ())
		)

		timestamp = self._from_date_to_int(datetime.now())

		pool = await self.channel_layer.connection(self.channel_layer.consistent_hash(group))
		with (await pool) as connection:
			for location in locations:
				await connection.zadd(location, (-1 if leave else 1) * timestamp, self.user.pk)

	async def get_users(self, group, room=None, only_active=True):
		pool = await self.channel_layer.connection(self.channel_layer.consistent_hash(group))
		presence_key = self._presence_key(group, room=room)
		now_timestamp = self._from_date_to_int(datetime.now())
		with (await pool) as connection:
			return [{
				'user': await sync_to_async(self.get_lazy_user)(user_pk),
				'present_at': self._from_int_to_date(timestamp),
				'active': True if now_timestamp - timestamp < self.expired_activity else False
			} for user_pk, timestamp in await connection.zrange(presence_key, start=0, end=-1, withscores=True)]

	@staticmethod
	def get_lazy_user(user_pk):
		return SimpleLazyObject(lambda: get_user_model().objects.get(pk=user_pk))

	def _presence_key(self, group, room=None):
		assert self.channel_layer.valid_group_name(group), "Group name not valid"
		group_key = self.channel_layer._group_key(group)

		return '{}:{}:presence'.format(group_key, room) if room else '{}:presence'.format(group_key)

	@staticmethod
	def _from_int_to_date(date):
		return datetime.fromtimestamp(date)

	@staticmethod
	def _from_date_to_int(date):
		return int(mktime(date.timetuple()))
