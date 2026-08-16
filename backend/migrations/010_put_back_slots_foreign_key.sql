alter table public.slots
    add constraint slots_rooms_room_id_fk
        foreign key (room_id) references public.rooms
            on delete cascade;