create table rooms
(
    room_id             varchar(50) not null
        constraint rooms_pk
            primary key,
    port                integer     not null,
    admin               varchar(50) not null,
    extract_folder_path varchar(255),
    arch_file_path      varchar(255),
    restarting          boolean,
    start               timestamp
);