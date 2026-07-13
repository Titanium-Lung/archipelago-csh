create table items
(
    game    varchar(255) not null,
    name    varchar(255),
    id      varchar(30)  not null,
    room_id varchar(50)  not null
        constraint items_rooms_room_id_fk
            references rooms
            on update cascade on delete cascade,
    constraint items_pk
        primary key (game, id, room_id)
);