class ShotService:

    def add_shot(
        self,
        shots,
        time_ms
    ):
        from core.shot import Shot

        shot = Shot(time_ms)

        shots.append(shot)

        shots.sort(
            key=lambda item:
            item.time_ms
        )

        return shot

    def delete_shot(
        self,
        shots,
        index
    ):
        if index < 0:
            return

        if index >= len(shots):
            return

        shots.pop(index)

    def update_note(
        self,
        shots,
        index,
        note
    ):
        if index < 0:
            return

        if index >= len(shots):
            return

        shots[index].note = note

    def sort_shots(
        self,
        shots
    ):
        shots.sort(
            key=lambda item:
            item.time_ms
        )
