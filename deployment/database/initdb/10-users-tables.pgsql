DROP TABLE IF EXISTS surfers CASCADE;
CREATE TABLE surfers (
	surfer_id UUID NOT NULL UNIQUE,
	project_id UUID,
	email TEXT NOT NULL,
	google_id TEXT DEFAULT '',
	is_admin BOOL NOT NULL DEFAULT false,
	is_email_verified BOOL NOT NULL,
	is_phone_verified BOOL NOT NULL,
	password TEXT DEFAULT '',

	email_confirm_token TEXT DEFAULT '',
	first_name TEXT DEFAULT '',
	last_name TEXT DEFAULT '',
	phone TEXT DEFAULT '',

	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (surfer_id)
);
CREATE INDEX idx_surfers_email ON surfers(email);


DROP TABLE IF EXISTS surfer_sessions CASCADE;
CREATE TABLE surfer_sessions (
	instance_id TEXT NOT NULL UNIQUE,
	surfer_id UUID NOT NULL,
	is_apple_session BOOL,
	is_google_session BOOL,
	jwt_long TEXT NOT NULL,
	platform TEXT NOT NULL,
	refresh_token_apple TEXT DEFAULT '',
	time_expires BIGINT DEFAULT 0,
	time_last_used BIGINT DEFAULT 0,
	time_next_24h_check BIGINT DEFAULT 0,
	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (instance_id)
);
CREATE INDEX idx_surfer_sessions_surfer_id ON surfer_sessions(surfer_id);


DROP TABLE IF EXISTS surfer_change_email_requests CASCADE;
CREATE TABLE surfer_change_email_requests (
	token TEXT NOT NULL,
	is_applied BOOL NOT NULL,
	is_consumed BOOL NOT NULL,
	surfer_id UUID NOT NULL,
	new_email TEXT,
	old_email TEXT,
	time_expires BIGINT DEFAULT 0,
	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (token)
);
CREATE INDEX idx_change_email_requests_surfer_id 
	ON surfer_change_email_requests(surfer_id);


DROP TABLE IF EXISTS surfer_change_password_requests CASCADE;
CREATE TABLE surfer_change_password_requests (
	token TEXT NOT NULL,
	is_consumed BOOL NOT NULL,
	surfer_id UUID NOT NULL,
	time_expires BIGINT DEFAULT 0,
	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (token)
);
CREATE INDEX idx_change_password_requests_surfer_id
	ON surfer_change_password_requests(surfer_id);


DROP TABLE IF EXISTS instances CASCADE;
CREATE TABLE instances (
	instance_id TEXT NOT NULL,
	platform TEXT DEFAULT '',
	time_last_used BIGINT DEFAULT 0,
	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (instance_id)
);
