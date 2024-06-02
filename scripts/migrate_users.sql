.echo ON
.backup db.back.sqlite3
.bail ON
.changes ON
.output
.trace 

# recreate the member table with a new name and containing all attributes of the user table
CREATE TABLE IF NOT EXISTS "members_member_new"(
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "password" varchar(128) NOT NULL,
  "last_login" datetime NULL,
  "is_superuser" bool NOT NULL,
  "username" varchar(150) NOT NULL UNIQUE,
  "first_name" varchar(150) NOT NULL,
  "last_name" varchar(150) NOT NULL,
  "email" varchar(254) NOT NULL,
  "is_staff" bool NOT NULL,
  "is_active" bool NOT NULL,
  "date_joined" datetime NOT NULL,
  "avatar" varchar(100) NULL,
  "phone" varchar(32) NOT NULL,
  "birthdate" date NULL,
  "website" varchar(200) NOT NULL,
  "description" text NULL,
  "hobbies" varchar(256) NULL,
  "managing_member_id" bigint NULL REFERENCES "members_member"("id") DEFERRABLE INITIALLY DEFERRED,
  "address_id" bigint NULL REFERENCES "members_address"("id") DEFERRABLE INITIALLY DEFERRED,
  "family_id" bigint NULL REFERENCES "members_family"("id") DEFERRABLE INITIALLY DEFERRED
);

#create associated indexes
CREATE INDEX "members_member_managing_member_id_b701e757" ON "members_member_new"( 
  "managing_member_id"
);
CREATE INDEX "members_member_new_address_id_d8dd8621" ON "members_member_new"(
  "address_id"
);
CREATE INDEX "members_mem_new_birthda_da42de_idx" ON "members_member_new"("birthdate");

# copy old member table + old user table content to new member table
INSERT INTO "members_member_new"(id, username, first_name, last_name,	email, is_staff, is_superuser, is_active, password,
	last_login, date_joined, avatar, phone, birthdate, website, description, family_id)
SELECT m.id, u.username, u.first_name, u.last_name,	u.email, u.is_staff, u.is_superuser, u.is_active, u.password,
	u.last_login, u.date_joined, m.avatar, m.phone, m.birthdate, m.website, m.description, m.family_id
FROM 
	members_member as m, 
	auth_user as u
WHERE m.account_id = u.id;

# recreate managing_member_id from old managing_account_id
update members_member_new
set
	managing_member_id = manager.mid
from 
	members_member,
	(select m.id as mid, u.id as uid from members_member_new as m, auth_user as u ) as manager
where members_member.managing_account_id <> ''
  and members_member.id = members_member_new.id
  and manager.uid = members_member.managing_account_id;

# replace account_id by member_id in chat messages
alter table chat_chatmessage add "member_id" bigint REFERENCES "members_member_new"("id") DEFERRABLE INITIALLY DEFERRED;
update chat_chatmessage
set member_id = ma.mid
from 
	(select m.id as mid, u.id as uid from members_member as m, auth_user as u where m.account_id=uid) as ma
where
	account_id = ma.uid;
# index new field
CREATE INDEX "chat_chatmessage_member_id_6dd68770" ON "chat_chatmessage"(
  "member_id"
);

# then drop old indexes before droping the old field
drop index chat_chatmessage_account_id_6dd68770;
alter table chat_chatmessage drop column account_id;



# replace author_id user ids by member ids in forum messages.
# first add a new field, then update it from old values
alter table forum_message add "author_id_new" bigint REFERENCES "members_member_new"("id") DEFERRABLE INITIALLY DEFERRED;
update forum_message
set author_id_new = ma.mid
from 
	(select m.id as mid, u.id as uid from members_member as m, auth_user as u where m.account_id=uid) as ma
where
	author_id = ma.uid;

# then drop old indexes before droping the old field, rename the new field and recreating the indexes
drop INDEX forum_messa_post_id_9ecfe0_idx;
drop INDEX forum_message_author_id_e031e57a;
alter table forum_message drop author_id;
alter table forum_message rename column author_id_new to author_id;
CREATE INDEX "forum_messa_post_id_9ecfe0_idx" ON "forum_message"(
  "post_id",
  "author_id"
);
CREATE INDEX "forum_message_author_id_e031e57a" ON "forum_message"(
  "author_id"
);


# replace author_id user ids by member ids in forum comments.
# first add a new field, then update it from old values
alter table forum_comment add "author_id_new" bigint REFERENCES "members_member_new"("id") DEFERRABLE INITIALLY DEFERRED;

update forum_comment
set author_id_new = ma.mid
from 
	(select m.id as mid, u.id as uid from members_member as m, auth_user as u where m.account_id=uid) as ma
where
	author_id = ma.uid;

# then drop old indexes before droping the old field, rename the new field and recreating the indexes
drop INDEX forum_comment_author_id_9e60eecd;
drop INDEX forum_comme_message_e8c1a7_idx;
alter table forum_comment drop author_id;
alter table forum_comment rename column author_id_new to author_id;
CREATE INDEX "forum_comment_author_id_9e60eecd" ON "forum_comment"(
  "author_id"
);
CREATE INDEX "forum_comme_message_e8c1a7_idx" ON "forum_comment"(
  "message_id",
  "author_id"
);


# replace requester_id user ids by member ids in verify_email_linkcounter.
# needs to go through the creation of a new table as requester_id as UNIQUE constraint
CREATE TABLE IF NOT EXISTS "verify_email_linkcounter_new"(
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "sent_count" integer NOT NULL,
  "requester_id" bigint NOT NULL UNIQUE REFERENCES "members_member"("id") DEFERRABLE INITIALLY DEFERRED
);

INSERT INTO "verify_email_linkcounter_new"(id, sent_count, requester_id)
SELECT v.id, v.sent_count, ma.mid
FROM 
	verify_email_linkcounter as v, 
	auth_user as u,
	(select m.id as mid, u.id as uid from members_member as m, auth_user as u where m.account_id=uid) as ma
WHERE v.requester_id = u.id and v.requester_id = ma.uid;

# then drop the old table and rename the new table
drop table verify_email_linkcounter;
alter table verify_email_linkcounter_new rename to verify_email_linkcounter;


# replace user_id user ids by member ids in django logs.
# first add a new field, then update it from old values
alter table django_admin_log add "user_id_new" bigint REFERENCES "members_member_new"("id") DEFERRABLE INITIALLY DEFERRED;

update django_admin_log
set user_id_new = ma.mid
from 
	(select m.id as mid, u.id as uid from members_member as m, auth_user as u where m.account_id=uid) as ma
where
	user_id = ma.uid;

# then drop old indexes before droping the old field, rename the new field and recreating the indexes
drop INDEX django_admin_log_user_id_c564eba6;
alter table django_admin_log drop user_id;
alter table django_admin_log rename column user_id_new to user_id;
CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log"(
  "user_id"
);





# drop old member table and rename the new one
DROP TABLE members_member;
alter table "members_member_new" rename to "members_member";


# drop old user related table
DROP TABLE auth_user;
DROP TABLE auth_user_groups;
DROP TABLE auth_user_user_permissions;

CREATE TABLE IF NOT EXISTS "members_member_groups"(
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "member_id" bigint NOT NULL REFERENCES "members_member"("id") DEFERRABLE INITIALLY DEFERRED,
  "group_id" integer NOT NULL REFERENCES "auth_group"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS "members_member_user_permissions"(
  "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
  "member_id" bigint NOT NULL REFERENCES "members_member"("id") DEFERRABLE INITIALLY DEFERRED,
  "permission_id" integer NOT NULL REFERENCES "auth_permission"("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE UNIQUE INDEX "members_member_groups_member_id_group_id_85fdd7e5_uniq" ON "members_member_groups"(
  "member_id",
  "group_id"
);
CREATE INDEX "members_member_groups_member_id_55ffa8d0" ON "members_member_groups"(
  "member_id"
);
CREATE INDEX "members_member_groups_group_id_03eaa557" ON "members_member_groups"(
  "group_id"
);
CREATE UNIQUE INDEX "members_member_user_permissions_member_id_permission_id_0020b208_uniq" ON "members_member_user_permissions"(
  "member_id",
  "permission_id"
);
CREATE INDEX "members_member_user_permissions_member_id_a0b158a9" ON "members_member_user_permissions"(
  "member_id"
);
CREATE INDEX "members_member_user_permissions_permission_id_8f87e59d" ON "members_member_user_permissions"(
  "permission_id"
);

.exit