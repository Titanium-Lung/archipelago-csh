create table slots
(
    id      integer     not null,
    name    varchar(20),
    game    varchar(255),
    room_id varchar(50) not null
        constraint slots_rooms_room_id_fk
            references rooms
            on delete cascade,
    constraint slots_pk
        primary key (id, room_id)
);