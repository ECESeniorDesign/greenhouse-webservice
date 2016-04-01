import models

def seed_controls():
    for control in ("fan", "pump", "light"):
        models.Control.create(name=control,
                              enabled=True,
                              active=False)

def seed_global_setting():
    models.GlobalSetting.create(notify_plants=True,
                                notify_maintenance=True)

def seed():
    seed_controls()
    seed_global_setting()
