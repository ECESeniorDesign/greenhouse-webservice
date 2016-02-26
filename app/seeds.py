import models

def seed_controls():
    for control in ("fan", "pump", "light"):
        models.Control.create(name=control,
                              enabled=True)

def seed():
    seed_controls()
