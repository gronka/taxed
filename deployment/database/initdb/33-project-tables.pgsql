DROP TABLE IF EXISTS projects CASCADE;
CREATE TABLE projects (
	project_id UUID NOT NULL UNIQUE,
	creator_id UUID NOT NULL,
	plan_id TEXT DEFAULT '',
	plan_id_next TEXT DEFAULT '',
	probius_id UUID,

	name TEXT DEFAULT '',
	notes TEXT DEFAULT '',
	time_plan_expires BIGINT DEFAULT 0,

	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (project_id),
	CONSTRAINT fk_projects_plan_id
		FOREIGN KEY (plan_id)
		REFERENCES plans(plan_id)
);


DROP TABLE IF EXISTS project_has_surfers CASCADE;
CREATE TABLE project_has_surfers (
	surfer_id UUID NOT NULL,
	project_id UUID NOT NULL,
	privilege TEXT DEFAULT '',
	time_created BIGINT DEFAULT 0,
	time_updated BIGINT DEFAULT 0,
	PRIMARY KEY (surfer_id, project_id),
	CONSTRAINT fk_project_has_surfers_to_projects_id
		FOREIGN KEY (project_id)
		REFERENCES projects(project_id),
	CONSTRAINT fk_project_has_surfers_to_surfer_id
		FOREIGN KEY (surfer_id)
		REFERENCES surfers(surfer_id) 
);
