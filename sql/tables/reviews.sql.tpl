create table if not exists `${sdomain}_reviews` (
    `id` integer primary key AUTOINCREMENT,
		`reviews` integer NOT NULL,
		`score` integer NOT NULL,
		`rank` integer NOT NULL,
		`name` varchar(256) NOT NULL,
		`desc` text NOT NULL,
    `surl` varchar(256) NOT NULL,
    `created` datetime NOT NULL,
    `updated` datetime NOT NULL
);
