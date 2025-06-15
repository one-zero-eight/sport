-- Script to prepare dump from production database for use in development.
-- It removes personal information and outdated rows from large tables.

DELETE FROM django_session WHERE bool(1)=true;
DELETE FROM django_admin_log WHERE bool(1)=true;
DELETE FROM medical_group_history WHERE bool(1)=true;
DELETE FROM medical_group_reference WHERE bool(1)=true;
DELETE FROM auth_user_groups WHERE group_id IN (
    SELECT id FROM auth_group
    WHERE name LIKE 'S-1-%' AND (verbose_name != 'Students' OR verbose_name is NULL)
);
DELETE FROM auth_group_permissions WHERE group_id IN (
    SELECT id FROM auth_group
    WHERE name LIKE 'S-1-%' AND (verbose_name != 'Students' OR verbose_name is NULL)
);
DELETE FROM auth_group
    WHERE name LIKE 'S-1-%' and (verbose_name != 'Students' OR verbose_name is NULL);
UPDATE auth_user SET password = '', last_login = NULL, last_name = '', date_joined = TIMESTAMP WITH TIME ZONE '2025-01-01 00:00:00+00' WHERE bool(1)=true;
UPDATE auth_user SET first_name = 'User ' || id, email = 'user' || id || '@innopolis.university' WHERE bool(1)=true;
UPDATE student SET telegram = NULL, comment = '', "has_QR" = false, is_online = false, sport_id = NULL WHERE bool(1)=true;
UPDATE self_sport_report SET image = NULL, link = NULL, uploaded = TIMESTAMP WITH TIME ZONE '2025-01-01 00:00:00+00', comment = '', student_comment = NULL, parsed_data = NULL WHERE bool(1)=true;
UPDATE reference SET image = '', uploaded = TIMESTAMP WITH TIME ZONE '2025-01-01 00:00:00+00', comment = NULL, student_comment = NULL WHERE bool(1)=true;

UPDATE student
SET gender = CASE (mod(abs(hashtext(user_id::text)), 3))
    WHEN 0 THEN -1
    WHEN 1 THEN 0
    WHEN 2 THEN 1
END
WHERE bool(1)=true;
UPDATE student
SET medical_group_id = CASE (mod(abs(hashtext(user_id::text)), 5))
    WHEN 0 THEN -2
    WHEN 1 THEN -1
    WHEN 2 THEN 0
    WHEN 3 THEN 1
    WHEN 4 THEN 2
END
WHERE bool(1)=true;
UPDATE sport_measurementresult
SET value = mod(abs(hashtext((id || '-' || measurement_id || '-' || session_id)::text)), 101)
WHERE bool(1)=true;
UPDATE sport_fitnesstestresult
SET value = mod(abs(hashtext((id || '-' || session_id || '-' || exercise_id || '-' || student_id)::text)), 101)
WHERE bool(1)=true;

DELETE FROM sport_trainingcheckin WHERE date < '2024-08-01';
DELETE FROM attendance AS a
USING public.training AS t
WHERE a.training_id = t.id
  AND t.start < '2024-08-01';
