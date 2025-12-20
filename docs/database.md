# Database setup
This project uses SQLite for testing and online services (e.g. Supabase) for actual usage.

# NOTE
This protocol will be replaced with a script which automates this processes.
For now, this is neccessary information.

# TESTING
1. The database file must be located at: data/quest.db
2. Open .env file and insert this link: DATABASE_URL=sqlite:///data/quest.db
3. Required table names: member, team, riddle (if changed, change the names in config too)
4. Member and team shall not be filled with data, riddle shall be.
5. To alter the database, enter in cmd: 'sqlite3 data/quest.db'
6. Creating table team:
CREATE TABLE team (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  start_stage INTEGER NOT NULL DEFAULT 0,
  cur_stage INTEGER NOT NULL DEFAULT 0,
  score INTEGER NOT NULL DEFAULT 0,
  cur_member_id INTEGER,
  stage_call_time INTEGER
);

7. Creating table member:
CREATE TABLE member (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tg_nickname TEXT,
  name TEXT NOT NULL,
  team_id INTEGER NOT NULL,

  FOREIGN KEY (team_id) REFERENCES team(id)
);

8. Creating table riddle:
CREATE TABLE riddle (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  type TEXT NOT NULL
);

9. Filling table riddle (example):
INSERT INTO riddle (question, answer, type) VALUES
('Что можно увидеть с закрытыми глазами?', 'сон', 'db'),
('Что становится больше, если из него вынимать?', 'яма', 'db'),
('Что принадлежит тебе, но другие используют чаще?', 'имя', 'db'),
('Без рук, без ног, а ворота открывает. Что это?', 'ветер', 'db'),
('Финальная загадка (тупик)', 'whatever', 'finale');

10. When you're done, type '.exit' in cmd.

Hooray, you've prepared your test database for the quest!
