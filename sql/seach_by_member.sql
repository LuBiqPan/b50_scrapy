
SELECT P.song_id, P.project_name, P.platform, P.amount, P.fanclub_id, P.remark
FROM
(
	SELECT id AS fanclub_id 
	FROM fanclubs
	WHERE member = '费沁源'
) AS F1
LEFT JOIN 
(
	SELECT *
	FROM projects
	WHERE is_obsolete = 0
) AS P 
ON F1.fanclub_id = P.fanclub_id

