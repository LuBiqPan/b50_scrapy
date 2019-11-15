
SELECT F1.song, F1.actress, F1.type, IFNULL(SUM(F1.amount), 0) AS amount
FROM
(
	SELECT S.song, S.type, S.actress, P.project_name, P.amount
	FROM songs AS S
	LEFT JOIN
    (
		SELECT song_id, project_name, amount 
        FROM projects
        WHERE is_obsolete = 0
    ) AS P ON S.id = P.song_id
) AS F1
GROUP BY F1.song, F1.actress, F1.type
ORDER BY F1.type, amount DESC;

