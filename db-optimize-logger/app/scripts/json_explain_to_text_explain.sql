-- From: https://github.com/david-rowley/json_explain_converter/blob/main/json_explain_to_text_explain.sql
CREATE OR REPLACE FUNCTION json_explain_to_text_explain(j json, do_analyze bool, do_verbose bool) RETURNS SETOF text AS
$$
DECLARE row RECORD;
BEGIN
	FOR row IN
		WITH RECURSIVE plan AS (
			SELECT
				json_array_element(j, 0)->'Plan' AS n,
				0 AS level,
				'' AS prefix,
				repeat(' ',2) AS detail_indent
			UNION ALL
			SELECT
				json_array_elements(n->'Plans') AS n,
				level + 1 AS level,
				repeat(' ', 6 * level) || '  ->  ' AS prefix,
				repeat(' ', (level + 1) * 8) AS detail_indent
			FROM plan
		)
		SELECT
			prefix,
			level,
			n,
			detail_indent,
			'(costs=' || (n->>'Startup Cost') || '..' || (n->>'Total Cost') || ' rows=' || (n->>'Plan Rows') || ' width=' || (n->'Plan Width') || ')' as costs,
			'  (actual time=' || (n->>'Actual Startup Time') || '..' || (n->>'Actual Total Time') || ' rows=' || (n->>'Actual Rows') || ' loop=' || (n->>'Actual Loops') || ')' as actual,
			CASE (n->>'Node Type')
				WHEN 'Seq Scan' THEN (n->>'Node Type') || ' on ' || COALESCE((n->>'Schema') || '.', '') || (n->>'Relation Name') || ' ' || (n->>'Alias')
				WHEN 'Index Scan' THEN (n->>'Node Type') || ' on ' || COALESCE((n->>'Schema') || '.', '') || (n->>'Relation Name') || ' ' || (n->>'Alias')
				WHEN 'Index Only Scan' THEN (n->>'Node Type') || ' on ' || COALESCE((n->>'Schema') || '.', '') || (n->>'Relation Name') || ' ' || (n->>'Alias')
				ELSE (n->>'Node Type')
			END AS node_name
		FROM plan
	LOOP
		RETURN NEXT row.prefix || row.node_name || '  ' || row.costs || CASE do_analyze WHEN true THEN COALESCE(row.actual,'') ELSE '' END;
		IF do_verbose = true AND row.n->'Output' IS NOT NULL THEN
			RETURN NEXT row.detail_indent || 'Output: ' || (SELECT string_agg(col::text, ', ') FROM json_array_elements(row.n->'Output') AS o(col));
		END IF;
		CASE (row.n->>'Node Type')
			WHEN 'Hash Join' THEN
				RETURN NEXT row.detail_indent || 'Hash Cond: ' || (row.n->>'Hash Cond');
			WHEN 'Sort' THEN
				RETURN NEXT row.detail_indent || 'Sort Key: ' || (SELECT string_agg(key::text, ', ') FROM json_array_elements(row.n->'Sort Key') AS s(key));
				RETURN NEXT row.detail_indent || 'Sort Method: ' || (row.n->>'Sort Method') || '  ' || (row.n->>'Sort Space Type') || ': ' || (row.n->>'Sort Space Used') || 'kB';
			WHEN 'Index Only Scan' THEN
				IF do_analyze = TRUE THEN
					RETURN NEXT row.detail_indent || 'Heap Fetches: ' || (row.n->>'Heap Fetches');
				END IF;
			WHEN 'Merge Join' THEN
				IF do_verbose = TRUE THEN
					RETURN NEXT row.detail_indent || 'Inner Unique: ' || (row.n->>'Inner Unique');
				END IF;
				RETURN NEXT row.detail_indent || 'Merge Cond: ' || (row.n->>'Merge Cond');
			WHEN 'Hash Join' THEN
				IF do_verbose = TRUE THEN
					RETURN NEXT row.detail_indent || 'Inner Unique: ' || (row.n->>'Inner Unique');
				END IF;
			WHEN 'Nested Loop' THEN
				IF do_verbose = TRUE THEN
					RETURN NEXT row.detail_indent || 'Inner Unique: ' || (row.n->>'Inner Unique');
				END IF;
			ELSE CONTINUE;
		END CASE;
	END LOOP;

	IF do_analyze = TRUE THEN
		RETURN NEXT 'Execution Time: ' || (json_array_element(j,0)->>'Execution Time');
	END IF;
END;
$$ LANGUAGE plpgsql;
