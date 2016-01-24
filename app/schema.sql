drop table if exists plants;
create table plants (
  id integer primary key autoincrement,
  name text not null,
  photo_url text not null,
  water_ideal real not null,
  water_tolerance real not null,
  light_ideal real not null,
  light_tolerance real not null,
  acidity_ideal real not null,
  acidity_tolerance real not null,
  humidity_ideal real not null,
  humidity_tolerance real not null,
  mature_on timestamp not null,
  slot_id integer not null unique,
  plant_database_id integer not null,
  created_at timestamp not null,
  updated_at timestamp not null
);

drop table if exists sensor_data_points;
create table sensor_data_points (
  id integer primary key autoincrement,
  plant_id integer not null,
  sensor_name text not null,
  sensor_value real not null,
  created_at timestamp not null,
  updated_at timestamp not null
);
