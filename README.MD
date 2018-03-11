**django-channels-presence2**

Simple presence boilerplate for django-channels 2 and channel redis backend.

**Installation**

`pip install django-channels-presence2`

**Usage**

Create presence for consumer:

```
self.presence = await ChannelPresence.create_from_consumer(self, groups=(PUBLICATIONS_SCHEDULE_GROUP,))
```

Example of create:

```
class Consumer(AsyncJsonWebsocketConsumer):
   async def connect(self):
       self.presence = await ChannelPresence.create_from_consumer(self, groups=(CONSUMER_GROUP,))
```
        
Groups are needed to send join and leave messages.
Learn more about groups: http://channels.readthedocs.io/en/latest/topics/channel_layers.html?highlight=group_send.     
        
Join user:

```
await self.presence.join()
```

Leave user:

```
await self.presence.leave()
```

Get users:

```
await self.presence.get_users(GROUP)
```

Return:

```
{
   'user': SimpleLazyObject of User,
   'is_active': True or False
   'present_at': Datetime
}
```

To set the activity expired time use `EXPIRED_USER_ACTIVITY` in django settings. 
