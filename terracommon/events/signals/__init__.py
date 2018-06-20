from django.dispatch import Signal, receiver

event = Signal(providing_args=['action', 'logged_user'])

def signal_event_proxy(*args, **kwargs):
    print(kwargs)

event.connect(signal_event_proxy)
