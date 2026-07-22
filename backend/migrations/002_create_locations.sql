create table locations
(
    slot          integer     not null,
    location_id   varchar(30) not null,
    sphere        integer,
    from_name     varchar(255),
    game          varchar(255),
    to_name       varchar(255),
    location_name varchar(255),
    item_name     varchar(255),
    room_id       varchar(50) not null
        constraint locations_rooms_room_id_fk
            references rooms
            on delete cascade,
    constraint locations_pk
        primary key (room_id, slot, location_id)
);