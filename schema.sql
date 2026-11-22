create table users (
    id INTEGER primary key AUTOINCREMENT,
    username text unique not null,
    email text unique not null,
    pwd_hash text not null 
);

create table contact (
    user_id INTEGER primary key,
    full_name varchar(50),
    phone text,
    location text,
    linkedin varchar(50),
    github varchar(50),
    portfolio varchar(50),
    foreign key (user_id) references users(id)
);

create table summary (
    user_id INTEGER primary key,
    content TEXT,
    foreign key (user_id) references users(id)
);

create table education (
    user_id int not null,
    education_id INTEGER primary key AUTOINCREMENT,
    institution text not null,
    degree text not null,
    field_of_study text not null,
    start_date date,
    end_date date,
    gpa TEXT not null,
    foreign key (user_id) references users(id)
);

create table experience (
    user_id INTEGER NOT NULL,
    exp_id INTEGER primary key AUTOINCREMENT,
    company text not null,
    role text not null,
    start_date date,
    end_date date,
    description text,
    foreign key (user_id) references users(id)
);

create table projects (
    user_id int not null,
    project_id INTEGER primary key AUTOINCREMENT,
    title text not null,
    description text,
    link text,
    start_date date,
    end_date date,
    foreign key (user_id) references users(id)
);

create table skills (
    skill_id INTEGER primary key AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skill_name text not null,
    foreign key (user_id) references users(id)

);
