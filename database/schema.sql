--
-- PostgreSQL database dump
--

\restrict zuQZWu1hBSM3iNGYr1LVULyAizXfCMg9Ij2HAWCVV79QUtmhVhoF2sp4U6VaacC

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: add_phone(integer, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.add_phone(f_user_id integer, f_phone_number text) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM phone_numbers WHERE phone_number = f_phone_number) THEN
        RAISE EXCEPTION 'Phone number already exists';
    END IF;
    
    INSERT INTO phone_numbers (user_id, phone_number)
    VALUES (f_user_id, f_phone_number);
    
    RETURN true;
END $$;


ALTER FUNCTION public.add_phone(f_user_id integer, f_phone_number text) OWNER TO postgres;

--
-- Name: assign_teacher_to_subject(integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.assign_teacher_to_subject(f_teacher_id integer, f_subject_id integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO staff_schedule (teacher_id, subject_id)
    VALUES (f_teacher_id, f_subject_id)
    ON CONFLICT DO NOTHING;
    
    RETURN true;
END $$;


ALTER FUNCTION public.assign_teacher_to_subject(f_teacher_id integer, f_subject_id integer) OWNER TO postgres;

--
-- Name: check_for_adulthood(date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.check_for_adulthood(f_birth_date date) RETURNS boolean
    LANGUAGE plpgsql
    AS $$

DECLARE
	f_age numeric;
BEGIN
	f_age := EXTRACT(YEAR FROM AGE(now(), f_birth_date));
	
	IF f_age >= 18 THEN
		RETURN true;
	ELSE
		RETURN false;
	END IF;
END $$;


ALTER FUNCTION public.check_for_adulthood(f_birth_date date) OWNER TO postgres;

--
-- Name: check_full_name(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.check_full_name(f_name text) RETURNS boolean
    LANGUAGE plpgsql
    AS $$

DECLARE
	name_splitted text[];
	l integer;
BEGIN
	name_splitted = string_to_array(f_name, ' ');
	l = array_length(name_splitted, 1);
	
	IF l <> 3 THEN
		RETURN false;
	ELSE
		RETURN true;
	END IF;
END $$;


ALTER FUNCTION public.check_full_name(f_name text) OWNER TO postgres;

--
-- Name: check_gender(character); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.check_gender(f_gender character) RETURNS boolean
    LANGUAGE plpgsql
    AS $$

BEGIN
	IF lower(f_gender) IN ('m', 'f') THEN
		RETURN true;
	ELSE
		RETURN false;
	END IF;
END $$;


ALTER FUNCTION public.check_gender(f_gender character) OWNER TO postgres;

--
-- Name: delete_mark(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.delete_mark(f_mark_id integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    DELETE FROM mark_log WHERE mark_id = f_mark_id;
    RETURN FOUND;
END $$;


ALTER FUNCTION public.delete_mark(f_mark_id integer) OWNER TO postgres;

--
-- Name: delete_parent(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.delete_parent(f_parent_id integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM parents_children WHERE parent_id = f_parent_id) THEN
        RAISE EXCEPTION 'Cannot delete parent: has children linked';
    END IF;
    
    DELETE FROM parents WHERE parent_id = f_parent_id;
    
    RETURN FOUND;
END $$;


ALTER FUNCTION public.delete_parent(f_parent_id integer) OWNER TO postgres;

--
-- Name: delete_pupil(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.delete_pupil(f_pupil_id integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_active_class BOOLEAN;
BEGIN
	IF EXISTS (SELECT 1 FROM pupils_classes WHERE pupil_id = f_pupil_id AND left_at IS NULL) THEN
        -- Сначала отчисляем
        PERFORM expel_pupil(f_pupil_id);
    END IF;
    
    DELETE FROM pupils WHERE pupil_id = f_pupil_id;
    
    RETURN FOUND;
END $$;


ALTER FUNCTION public.delete_pupil(f_pupil_id integer) OWNER TO postgres;

--
-- Name: delete_teacher(integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.delete_teacher(f_teacher_id integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_active_classes INT;
BEGIN
    -- Проверка: не является ли классным руководителем активных классов
    SELECT COUNT(*) INTO v_active_classes
    FROM classes AS c
    JOIN staff AS s ON c.school_id = s.school_id
    WHERE c.class_teacher_id = f_teacher_id 
      AND s.fired_at IS NULL;
    
    IF v_active_classes > 0 THEN
        RAISE EXCEPTION 'Cannot delete teacher: is active class teacher';
    END IF;
    
    DELETE FROM teachers WHERE teacher_id = f_teacher_id;
    RETURN FOUND;
END $$;


ALTER FUNCTION public.delete_teacher(f_teacher_id integer) OWNER TO postgres;

--
-- Name: enroll_pupil(integer, integer, date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.enroll_pupil(f_pupil_id integer, f_class_id integer, f_entered_at date DEFAULT CURRENT_DATE) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
	v_p_count INT;
BEGIN
    -- Проверка: ученик не должен быть активен в другом классе
    IF EXISTS (
        SELECT 1 FROM pupils_classes 
        WHERE pupil_id = f_pupil_id AND left_at IS NULL
    ) THEN
        RAISE EXCEPTION 'Pupil is already enrolled in another class';
    END IF;

	SELECT pupil_count INTO v_p_count
	FROM classes
	WHERE class_id = f_class_id;

	IF v_p_count = 30 THEN
		RAISE EXCEPTION 'Class already consists of 30 pupils. You cannot add more';
	END IF;
    
    INSERT INTO pupils_classes (pupil_id, class_id, entered_at)
    VALUES (f_pupil_id, f_class_id, f_entered_at);
    
    -- Обновляем счетчик учеников
    UPDATE classes SET pupil_count = pupil_count + 1 
    WHERE class_id = f_class_id;
    
    RETURN true;
END $$;


ALTER FUNCTION public.enroll_pupil(f_pupil_id integer, f_class_id integer, f_entered_at date) OWNER TO postgres;

--
-- Name: expel_pupil(integer, date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.expel_pupil(f_pupil_id integer, f_left_at date DEFAULT CURRENT_DATE) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_class_id INT;
BEGIN
    -- Находим активный класс ученика
    SELECT class_id INTO v_class_id
    FROM pupils_classes 
    WHERE pupil_id = f_pupil_id AND left_at IS NULL;
    
    IF NOT FOUND THEN
        RAISE SQLSTATE '22023' USING
			message := 'Pupil is not enrolled in any class';
    END IF;
    
    -- Закрываем запись
    UPDATE pupils_classes 
    SET left_at = f_left_at 
    WHERE pupil_id = f_pupil_id AND left_at IS NULL;
    
    -- Обновляем счетчик учеников
    UPDATE classes SET pupil_count = pupil_count - 1 
    WHERE class_id = v_class_id;
    
    RETURN true;
END $$;


ALTER FUNCTION public.expel_pupil(f_pupil_id integer, f_left_at date) OWNER TO postgres;

--
-- Name: fire_teacher(integer, integer, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.fire_teacher(f_teacher_id integer, f_school_id integer, f_fired_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_hired_at TIMESTAMP;
BEGIN
    -- Получаем дату найма
    SELECT hired_at INTO v_hired_at
    FROM staff 
    WHERE worker_id = f_teacher_id AND school_id = f_school_id AND fired_at IS NULL;
    
    IF NOT FOUND THEN
        RAISE SQLSTATE '22023' USING
			message := 'Teacher is not currently employed at this school';
    END IF;
    
    IF f_fired_at <= v_hired_at THEN
        RAISE SQLSTATE '22023' USING
			message := 'Firing date must be after hiring date';
    END IF;
    
    UPDATE staff 
    SET fired_at = f_fired_at 
    WHERE worker_id = f_teacher_id AND school_id = f_school_id AND fired_at IS NULL;
    
    RETURN true;
END $$;


ALTER FUNCTION public.fire_teacher(f_teacher_id integer, f_school_id integer, f_fired_at timestamp without time zone) OWNER TO postgres;

--
-- Name: format_phone(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.format_phone() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF LENGTH(phone_number) = 10 THEN
        NEW.phone_number := regexp_replace(NEW.phone_number,'(\d{3})(\d{3})(\d{2})(\d{2})', '(\1)\2-\3-\4');
	ELSE
		RAISE EXCEPTION 'phone_number must contain 10 digits.';
    END IF;
	RETURN NEW;
END $$;


ALTER FUNCTION public.format_phone() OWNER TO postgres;

--
-- Name: hire_teacher(integer, integer, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.hire_teacher(f_teacher_id integer, f_school_id integer, f_hired_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Проверка: учитель не должен быть уже трудоустроен в эту школу
    IF EXISTS (
        SELECT 1 FROM staff 
        WHERE worker_id = f_teacher_id 
          AND school_id = f_school_id 
          AND fired_at IS NULL
    ) THEN
        RAISE EXCEPTION 'Teacher is already hired in this school';
    END IF;
    
    INSERT INTO staff (worker_id, school_id, hired_at)
    VALUES (f_teacher_id, f_school_id, f_hired_at);
    
    RETURN TRUE;
END $$;


ALTER FUNCTION public.hire_teacher(f_teacher_id integer, f_school_id integer, f_hired_at timestamp without time zone) OWNER TO postgres;

--
-- Name: insert_class(integer, integer, character, integer, integer, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.insert_class(f_school_id integer, f_class_teacher_id integer, f_letter character, f_form_year integer, f_c_number integer DEFAULT 0, f_cabinet text DEFAULT NULL::text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_class_id integer;
BEGIN
    -- Проверка уникальности класса в школе
    IF EXISTS (
        SELECT 1 FROM classes 
        WHERE school_id = f_school_id 
          AND c_number = f_c_number 
          AND letter = f_letter 
          AND form_year = f_form_year
    ) THEN
        RAISE EXCEPTION 'Class with this number, letter and year already exists in this school';
    END IF;
    
    INSERT INTO classes (school_id, class_teacher_id, letter, form_year, cabinet, c_number)
    VALUES (f_school_id, f_class_teacher_id, f_letter, f_form_year, f_cabinet, f_c_number)
    RETURNING class_id INTO v_class_id;
    
    RETURN v_class_id;
END $$;


ALTER FUNCTION public.insert_class(f_school_id integer, f_class_teacher_id integer, f_letter character, f_form_year integer, f_c_number integer, f_cabinet text) OWNER TO postgres;

--
-- Name: insert_mark(integer, integer, integer, integer, text, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.insert_mark(f_subject_id integer, f_teacher_id integer, f_pupil_id integer, f_mark_value integer, f_assessment_form text, f_put_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_mark_id INT;
    v_valid_forms TEXT[] := ARRAY['homework', 'classwork', 'word_dictation', 
                                   'independent_work', 'dictation', 'medium_test', 
                                   'report', 'abstract', 'final_test'];
BEGIN
    -- Проверка значения оценки
    IF f_mark_value < 2 OR f_mark_value > 5 THEN
        RAISE EXCEPTION 'Mark value must be between 2 and 5';
    END IF;
    
    -- Проверка формы контроля
    IF NOT (f_assessment_form = ANY(v_valid_forms)) THEN
        RAISE EXCEPTION 'Invalid assessment form';
    END IF;
    
    -- Проверка: учитель ведет этот предмет
    IF NOT EXISTS (
        SELECT 1 FROM staff_schedule 
        WHERE teacher_id = f_teacher_id AND subject_id = f_subject_id
    ) THEN
        RAISE EXCEPTION 'Teacher does not teach this subject';
    END IF;
    
    -- Проверка: ученик активен в классе
    IF NOT EXISTS (
        SELECT 1 FROM pupils_classes 
        WHERE pupil_id = f_pupil_id AND left_at IS NULL
    ) THEN
        RAISE EXCEPTION 'Pupil is not currently enrolled';
    END IF;
    
    INSERT INTO mark_log (subject_id, teacher_id, pupil_id, mark_value, assessment_form, put_at)
    VALUES (f_subject_id, f_teacher_id, f_pupil_id, f_mark_value, f_assessment_form, f_put_at)
    RETURNING mark_id INTO v_mark_id;
    
    RETURN v_mark_id;
END $$;


ALTER FUNCTION public.insert_mark(f_subject_id integer, f_teacher_id integer, f_pupil_id integer, f_mark_value integer, f_assessment_form text, f_put_at timestamp without time zone) OWNER TO postgres;

--
-- Name: insert_parent_account(text, text, text, text, character, date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.insert_parent_account(f_login text, f_password_hash text, f_full_name text, f_address text, f_gender character, f_birth_date date DEFAULT NULL::date) RETURNS integer
    LANGUAGE plpgsql
    AS $$

DECLARE
    v_parent_id INTEGER;
BEGIN
	-- Валидация
    IF NOT public.check_gender(f_gender) THEN
        RAISE EXCEPTION 'gender must be m/M or f/F';
    END IF;
    
    IF NOT public.check_full_name(f_full_name) THEN
        RAISE EXCEPTION 'full_name must be like "first_name last_name patronymic"';
    END IF;
    
    -- Создание аккаунта
    INSERT INTO accounts (login, password_hash, u_role)
    VALUES (f_login, f_password_hash, 'parent')
    RETURNING user_id INTO v_parent_id;
    
    -- Создание сущности
    INSERT INTO parents (parent_id, full_name, address, gender, birth_date)
    VALUES (v_parent_id, f_full_name, f_address, lower(f_gender), f_birth_date);
    
    RETURN v_parent_id;
END $$;


ALTER FUNCTION public.insert_parent_account(f_login text, f_password_hash text, f_full_name text, f_address text, f_gender character, f_birth_date date) OWNER TO postgres;

--
-- Name: insert_pupil_account(text, text, text, text, character, date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.insert_pupil_account(f_login text, f_password_hash text, f_full_name text, f_address text, f_gender character, f_birth_date date) RETURNS integer
    LANGUAGE plpgsql
    AS $$

DECLARE
    v_pupil_id INTEGER;
BEGIN
	-- Валидация
    IF NOT public.check_gender(f_gender) THEN
        RAISE EXCEPTION 'gender must be m/M or f/F';
    END IF;
    
    IF NOT public.check_full_name(f_full_name) THEN
        RAISE EXCEPTION 'full_name must be like "first_name last_name patronymic"';
    END IF;
    
    -- Создание аккаунта
    INSERT INTO accounts (login, password_hash, u_role)
    VALUES (f_login, f_password_hash, 'pupil')
    RETURNING user_id INTO v_pupil_id;
    
    -- Создание сущности
    INSERT INTO pupils (pupil_id, full_name, address, gender, birth_date)
    VALUES (v_pupil_id, f_full_name, f_address, lower(f_gender), f_birth_date);
    
    RETURN v_pupil_id;
END $$;


ALTER FUNCTION public.insert_pupil_account(f_login text, f_password_hash text, f_full_name text, f_address text, f_gender character, f_birth_date date) OWNER TO postgres;

--
-- Name: insert_school(text, text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.insert_school(f_title text, f_address text, f_established_in integer DEFAULT NULL::integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$

DECLARE
	v_school_id integer;
BEGIN
	INSERT INTO schools (title, established_in, address)
	VALUES (f_title, f_established_in, f_address)
	RETURNING school_id INTO v_school_id;
	RETURN v_school_id;
END $$;


ALTER FUNCTION public.insert_school(f_title text, f_address text, f_established_in integer) OWNER TO postgres;

--
-- Name: insert_subject(text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.insert_subject(f_title text) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_subject_id INT;
BEGIN
    INSERT INTO subjects (title) VALUES (f_title)
    RETURNING subject_id INTO v_subject_id;
    
    RETURN v_subject_id;
END $$;


ALTER FUNCTION public.insert_subject(f_title text) OWNER TO postgres;

--
-- Name: insert_teacher_account(text, text, text, text, character, date, text, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.insert_teacher_account(f_login text, f_password_hash text, f_full_name text, f_address text, f_gender character, f_birth_date date, f_emp_rec_book_num text, f_head_teacher boolean DEFAULT false) RETURNS integer
    LANGUAGE plpgsql
    AS $$

DECLARE
    v_teacher_id INTEGER;
	v_role TEXT;
BEGIN
    -- Валидация
    IF NOT public.check_gender(f_gender) THEN
        RAISE EXCEPTION 'gender must be m/M or f/F';
    END IF;
    
    IF NOT public.check_full_name(f_full_name) THEN
        RAISE EXCEPTION 'full_name must be like "first_name last_name patronymic"';
    END IF;
    
    IF NOT public.check_for_adulthood(f_birth_date) THEN
        RAISE EXCEPTION 'Teacher must be older than 18';
    END IF;

	IF f_head_teacher THEN
		v_role := 'headteacher';
	ELSE
		v_role := 'teacher';
	END IF;
	
    -- Создание аккаунта
    INSERT INTO accounts (login, password_hash, u_role)
    VALUES (f_login, f_password_hash, v_role)
    RETURNING user_id INTO v_teacher_id;
    
    -- Создание сущности
    INSERT INTO teachers (teacher_id, full_name, address, gender, birth_date, 
                          emp_rec_book_num, head_teacher)
    VALUES (v_teacher_id, f_full_name, f_address, lower(f_gender), 
            f_birth_date, f_emp_rec_book_num, f_head_teacher);
    
    RETURN v_teacher_id;
END $$;


ALTER FUNCTION public.insert_teacher_account(f_login text, f_password_hash text, f_full_name text, f_address text, f_gender character, f_birth_date date, f_emp_rec_book_num text, f_head_teacher boolean) OWNER TO postgres;

--
-- Name: link_parent_child(integer, integer, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.link_parent_child(f_parent_id integer, f_child_id integer, f_relation_type text) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
	IF lower(f_relation_type) NOT IN ('mother', 'father', 'guardian', 'grandmother', 'grandfather') THEN
        RAISE EXCEPTION 'Unsopported relation type';
    END IF;

    INSERT INTO parents_children (parent_id, child_id, relation_type)
    VALUES (f_parent_id, f_child_id, f_relation_type)
    ON CONFLICT DO NOTHING;
    
    RETURN true;
END $$;


ALTER FUNCTION public.link_parent_child(f_parent_id integer, f_child_id integer, f_relation_type text) OWNER TO postgres;

--
-- Name: recalc_performance_for_pupil_subject(integer, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.recalc_performance_for_pupil_subject(f_pupil_id integer, f_subject_id integer) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_mark_total INTEGER := 0;
    v_weights_sum INTEGER := 0;
    v_final_mark INTEGER := 0;
    v_weight INTEGER;
    v_mark_value INTEGER;
    v_record_exists BOOLEAN;
BEGIN
    -- Определяем вес для каждой формы контроля
    FOR v_mark_value, v_weight IN
        SELECT ml.mark_value,
               CASE ml.assessment_form
                   WHEN 'homework' THEN 1
                   WHEN 'classwork' THEN 2
                   WHEN 'word_dictation' THEN 2
                   WHEN 'independent_work' THEN 3
                   WHEN 'dictation' THEN 3
                   WHEN 'medium_test' THEN 4
                   WHEN 'report' THEN 4
                   WHEN 'abstract' THEN 4
                   WHEN 'final_test' THEN 5
                   ELSE 1
               END AS weight
        FROM mark_log ml
        WHERE ml.pupil_id = f_pupil_id 
          AND ml.subject_id = f_subject_id
    LOOP
        v_mark_total := v_mark_total + (v_mark_value * v_weight);
        v_weights_sum := v_weights_sum + v_weight;
    END LOOP;
    
    -- Вычисляем итоговую оценку (средневзвешенная, округленная)
    IF v_weights_sum > 0 THEN
        v_final_mark := ROUND(v_mark_total::NUMERIC / v_weights_sum);
        -- Ограничиваем диапазоном 2-5
        IF v_final_mark < 2 THEN
            v_final_mark := 2;
        ELSIF v_final_mark > 5 THEN
            v_final_mark := 5;
        END IF;
    END IF;
    
    -- Проверяем, существует ли уже запись в performance_report
    SELECT EXISTS(
        SELECT 1 FROM performance_report 
        WHERE pupil_id = f_pupil_id AND subject_id = f_subject_id
    ) INTO v_record_exists;
    
    -- Обновляем или вставляем
    IF v_record_exists THEN
        UPDATE performance_report 
        SET mark_total = v_mark_total,
            weights_sum = v_weights_sum,
            final_mark = v_final_mark
        WHERE pupil_id = f_pupil_id AND subject_id = f_subject_id;
    ELSE
        INSERT INTO performance_report (pupil_id, subject_id, mark_total, weights_sum, final_mark)
        VALUES (f_pupil_id, f_subject_id, v_mark_total, v_weights_sum, v_final_mark);
    END IF;
END $$;


ALTER FUNCTION public.recalc_performance_for_pupil_subject(f_pupil_id integer, f_subject_id integer) OWNER TO postgres;

--
-- Name: trigger_update_performance_report(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.trigger_update_performance_report() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- При вставке или обновлении: пересчитываем
    IF TG_OP = 'INSERT' THEN
        PERFORM recalc_performance_for_pupil_subject(NEW.pupil_id, NEW.subject_id);
        
    ELSIF TG_OP = 'UPDATE' THEN
        -- Если изменился pupil_id или subject_id, нужно пересчитать для старой и новой комбинации
        IF NEW.pupil_id != OLD.pupil_id OR NEW.subject_id != OLD.subject_id THEN
            PERFORM recalc_performance_for_pupil_subject(OLD.pupil_id, OLD.subject_id);
            PERFORM recalc_performance_for_pupil_subject(NEW.pupil_id, NEW.subject_id);
        ELSE
            -- Иначе только для текущей комбинации
            PERFORM recalc_performance_for_pupil_subject(NEW.pupil_id, NEW.subject_id);
        END IF;
        
    ELSIF TG_OP = 'DELETE' THEN
        -- При удалении пересчитываем для удаленной комбинации
        PERFORM recalc_performance_for_pupil_subject(OLD.pupil_id, OLD.subject_id);
    END IF;
    
    RETURN NULL;
END $$;


ALTER FUNCTION public.trigger_update_performance_report() OWNER TO postgres;

--
-- Name: update_account_login(integer, text, text); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_account_login(f_user_id integer, f_login text, f_password_hash text DEFAULT NULL::text) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE accounts 
    SET login = f_login,
        password_hash = COALESCE(f_password_hash, password_hash)
    WHERE user_id = f_user_id;
    
    RETURN FOUND;
END $$;


ALTER FUNCTION public.update_account_login(f_user_id integer, f_login text, f_password_hash text) OWNER TO postgres;

--
-- Name: update_mark(integer, integer, text, timestamp without time zone); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_mark(f_mark_id integer, f_mark_value integer DEFAULT NULL::integer, f_assessment_form text DEFAULT NULL::text, f_put_at timestamp without time zone DEFAULT NULL::timestamp without time zone) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_valid_forms TEXT[] := ARRAY['homework', 'classwork', 'word_dictation', 
                                   'independent_work', 'dictation', 'medium_test', 
                                   'report', 'abstract', 'final_test'];
    v_old_pupil_id INTEGER;
    v_old_subject_id INTEGER;
    v_old_mark_value INTEGER;
    v_new_pupil_id INTEGER;
    v_new_subject_id INTEGER;
BEGIN
    -- Получаем старые значения
    SELECT pupil_id, subject_id, mark_value 
    INTO v_old_pupil_id, v_old_subject_id, v_old_mark_value
    FROM mark_log 
    WHERE mark_id = f_mark_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Mark with id % not found', f_mark_id;
    END IF;
    
    -- Проверка значения оценки
    IF f_mark_value IS NOT NULL AND (f_mark_value < 2 OR f_mark_value > 5) THEN
        RAISE EXCEPTION 'Mark value must be between 2 and 5';
    END IF;
    
    -- Проверка формы контроля
    IF f_assessment_form IS NOT NULL AND NOT (f_assessment_form = ANY(v_valid_forms)) THEN
        RAISE EXCEPTION 'Invalid assessment form: %', f_assessment_form;
    END IF;
    
    -- Выполняем обновление
    UPDATE mark_log 
    SET mark_value = COALESCE(f_mark_value, mark_value),
        assessment_form = COALESCE(f_assessment_form, assessment_form),
        put_at = COALESCE(f_put_at, put_at)
    WHERE mark_id = f_mark_id;
    
    RETURN FOUND;
END $$;


ALTER FUNCTION public.update_mark(f_mark_id integer, f_mark_value integer, f_assessment_form text, f_put_at timestamp without time zone) OWNER TO postgres;

--
-- Name: update_parent(integer, text, text, character, date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_parent(f_parent_id integer, f_full_name text, f_address text, f_gender character, f_birth_date date DEFAULT NULL::date) RETURNS integer
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NOT check_gender(f_gender) THEN
        RAISE EXCEPTION 'gender must be m/M or f/F';
    END IF;
    
    IF NOT check_full_name(f_full_name) THEN
        RAISE EXCEPTION 'full_name must be like "first_name last_name patronymic"';
    END IF;
    
    UPDATE parents 
    SET full_name = f_full_name,
        address = f_address,
        gender = lower(f_gender),
        birth_date = f_birth_date
    WHERE parent_id = f_parent_id;
    
    RETURN f_parent_id;
END $$;


ALTER FUNCTION public.update_parent(f_parent_id integer, f_full_name text, f_address text, f_gender character, f_birth_date date) OWNER TO postgres;

--
-- Name: update_pupil(integer, text, text, character, date); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_pupil(f_pupil_id integer, f_full_name text, f_address text, f_gender character, f_birth_date date) RETURNS integer
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NOT check_gender(f_gender) THEN
        RAISE EXCEPTION 'gender must be m/M or f/F';
    END IF;
    
    IF NOT check_full_name(f_full_name) THEN
        RAISE EXCEPTION 'full_name must be like "first_name last_name patronymic"';
    END IF;
    
    UPDATE pupils 
    SET full_name = f_full_name,
        address = f_address,
        gender = lower(f_gender),
        birth_date = f_birth_date
    WHERE pupil_id = f_pupil_id;
    
    RETURN f_pupil_id;
END $$;


ALTER FUNCTION public.update_pupil(f_pupil_id integer, f_full_name text, f_address text, f_gender character, f_birth_date date) OWNER TO postgres;

--
-- Name: update_school(integer, text, text, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_school(f_school_id integer, f_title text, f_address text, f_established_in integer DEFAULT NULL::integer) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN    
    UPDATE schools 
    SET title = f_title,
		address = f_address,
		established_in = f_established_in
    WHERE school_id = f_school_id;
    
    RETURN true;
END $$;


ALTER FUNCTION public.update_school(f_school_id integer, f_title text, f_address text, f_established_in integer) OWNER TO postgres;

--
-- Name: update_teacher(integer, text, text, character, date, text, boolean); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_teacher(f_user_id integer, f_full_name text, f_address text, f_gender character, f_birth_date date, f_emp_rec_book_num text, f_head_teacher boolean) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE teachers 
    SET full_name = f_full_name,
        address = f_address,
        gender = lower(f_gender),
        birth_date = f_birth_date,
        emp_rec_book_num = f_emp_rec_book_num,
        head_teacher = f_head_teacher
    WHERE user_id = f_user_id;
    
    RETURN FOUND;
END $$;


ALTER FUNCTION public.update_teacher(f_user_id integer, f_full_name text, f_address text, f_gender character, f_birth_date date, f_emp_rec_book_num text, f_head_teacher boolean) OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accounts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accounts (
    user_id integer NOT NULL,
    login text NOT NULL,
    password_hash text NOT NULL,
    created_at timestamp(0) with time zone DEFAULT now() NOT NULL,
    u_role text CONSTRAINT accounts_role_not_null NOT NULL
);


ALTER TABLE public.accounts OWNER TO postgres;

--
-- Name: accounts_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.accounts ALTER COLUMN user_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.accounts_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: classes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.classes (
    class_id integer NOT NULL,
    school_id integer NOT NULL,
    class_teacher_id integer NOT NULL,
    letter "char" NOT NULL,
    form_year integer NOT NULL,
    cabinet text,
    pupil_count integer DEFAULT 0 NOT NULL,
    c_number integer NOT NULL
);


ALTER TABLE public.classes OWNER TO postgres;

--
-- Name: classes_class_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.classes ALTER COLUMN class_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.classes_class_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: mark_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mark_log (
    mark_id integer NOT NULL,
    subject_id integer NOT NULL,
    teacher_id integer NOT NULL,
    pupil_id integer NOT NULL,
    mark_value integer NOT NULL,
    put_at timestamp(0) with time zone DEFAULT now() NOT NULL,
    assessment_form text NOT NULL
);


ALTER TABLE public.mark_log OWNER TO postgres;

--
-- Name: mark_log_mark_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.mark_log ALTER COLUMN mark_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.mark_log_mark_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: parents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parents (
    parent_id integer NOT NULL,
    full_name text NOT NULL,
    address text NOT NULL,
    birth_date date,
    gender "char" NOT NULL
);


ALTER TABLE public.parents OWNER TO postgres;

--
-- Name: parents_children; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.parents_children (
    child_id integer NOT NULL,
    parent_id integer NOT NULL,
    relation_type text NOT NULL
);


ALTER TABLE public.parents_children OWNER TO postgres;

--
-- Name: performance_report; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.performance_report (
    pupil_id integer NOT NULL,
    subject_id integer NOT NULL,
    mark_total integer NOT NULL,
    weights_sum integer NOT NULL,
    final_mark integer NOT NULL
);


ALTER TABLE public.performance_report OWNER TO postgres;

--
-- Name: phone_numbers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.phone_numbers (
    user_id integer NOT NULL,
    phone_number text NOT NULL
);


ALTER TABLE public.phone_numbers OWNER TO postgres;

--
-- Name: pupils; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pupils (
    pupil_id integer NOT NULL,
    full_name text NOT NULL,
    address text NOT NULL,
    birth_date date NOT NULL,
    gender "char" NOT NULL
);


ALTER TABLE public.pupils OWNER TO postgres;

--
-- Name: pupils_classes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pupils_classes (
    pupil_id integer NOT NULL,
    class_id integer NOT NULL,
    entered_at date NOT NULL,
    left_at date
);


ALTER TABLE public.pupils_classes OWNER TO postgres;

--
-- Name: responsibilities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.responsibilities (
    head_teacher_id integer NOT NULL,
    responsibility text NOT NULL
);


ALTER TABLE public.responsibilities OWNER TO postgres;

--
-- Name: schools; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.schools (
    school_id integer NOT NULL,
    title text NOT NULL,
    established_in integer,
    address text NOT NULL
);


ALTER TABLE public.schools OWNER TO postgres;

--
-- Name: schools_school_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.schools ALTER COLUMN school_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.schools_school_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: staff; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.staff (
    worker_id integer NOT NULL,
    school_id integer NOT NULL,
    hired_at timestamp(0) with time zone DEFAULT now() NOT NULL,
    fired_at timestamp(0) with time zone
);


ALTER TABLE public.staff OWNER TO postgres;

--
-- Name: staff_schedule; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.staff_schedule (
    teacher_id integer NOT NULL,
    subject_id integer NOT NULL
);


ALTER TABLE public.staff_schedule OWNER TO postgres;

--
-- Name: subjects; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.subjects (
    subject_id integer NOT NULL,
    title text NOT NULL
);


ALTER TABLE public.subjects OWNER TO postgres;

--
-- Name: subjects_subject_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.subjects ALTER COLUMN subject_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.subjects_subject_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: teachers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.teachers (
    teacher_id integer NOT NULL,
    full_name text NOT NULL,
    address text NOT NULL,
    birth_date date NOT NULL,
    gender "char" NOT NULL,
    head_teacher boolean DEFAULT false NOT NULL,
    emp_rec_book_num text NOT NULL
);


ALTER TABLE public.teachers OWNER TO postgres;

--
-- Data for Name: accounts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.accounts (user_id, login, password_hash, created_at, u_role) FROM stdin;
1	ivanova.ann	hash_ivanova123	2026-06-12 17:17:46+05	headteacher
2	petrov.sergey	hash_petrov456	2026-06-12 17:17:46+05	teacher
3	sidorova.elena	hash_sidorova789	2026-06-12 17:17:46+05	headteacher
4	alekseev.dima	hash_dima123	2026-06-12 17:17:46+05	pupil
5	belova.nastya	hash_nastya456	2026-06-12 17:17:46+05	pupil
6	volkov.maxim	hash_maxim789	2026-06-12 17:17:46+05	pupil
7	grigorieva.katya	hash_katya101	2026-06-12 17:17:46+05	pupil
8	denisov.artem	hash_artem112	2026-06-12 17:17:46+05	pupil
9	emelyanova.sofia	hash_sofia131	2026-06-12 17:17:46+05	pupil
10	zhukov.timofey	hash_timofey415	2026-06-12 17:17:46+05	pupil
11	zaytseva.polina	hash_polina161	2026-06-12 17:17:46+05	pupil
12	ivanov.nikita	hash_nikita718	2026-06-12 17:17:46+05	pupil
13	kuznetsova.varvara	hash_varvara192	2026-06-12 17:17:46+05	pupil
14	alekseev.andrey	hash_parent001	2026-06-12 17:17:46+05	parent
15	belova.svetlana	hash_parent002	2026-06-12 17:17:46+05	parent
16	volkova.olga	hash_parent003	2026-06-12 17:17:46+05	parent
17	grigoriev.dmitry	hash_parent004	2026-06-12 17:17:46+05	parent
18	denisova.marina	hash_parent005	2026-06-12 17:17:46+05	parent
19	emelyanova.elena	hash_parent006	2026-06-12 17:17:46+05	parent
20	zhukov.mikhail	hash_parent007	2026-06-12 17:17:46+05	parent
21	zaytseva.irina	hash_parent008	2026-06-12 17:17:46+05	parent
22	ivanova.tatyana	hash_parent009	2026-06-12 17:17:46+05	parent
23	kuznetsov.andrey	hash_parent010	2026-06-12 17:17:46+05	parent
\.


--
-- Data for Name: classes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.classes (class_id, school_id, class_teacher_id, letter, form_year, cabinet, pupil_count, c_number) FROM stdin;
2	1	3	b	2025	cabinet 102	5	5
1	1	1	a	2025	cabinet 101	5	5
\.


--
-- Data for Name: mark_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mark_log (mark_id, subject_id, teacher_id, pupil_id, mark_value, put_at, assessment_form) FROM stdin;
1	1	1	4	4	2024-09-15 10:00:00+05	classwork
2	1	1	4	5	2024-09-16 14:00:00+05	homework
3	2	1	4	3	2024-09-17 09:00:00+05	dictation
4	2	1	4	4	2024-09-18 13:00:00+05	homework
5	4	2	4	5	2024-09-19 11:00:00+05	classwork
6	4	2	4	4	2024-09-20 15:00:00+05	homework
7	1	1	5	5	2024-09-15 10:00:00+05	classwork
8	1	1	5	5	2024-09-20 10:00:00+05	medium_test
9	3	1	5	4	2024-09-16 12:00:00+05	classwork
10	3	1	5	5	2024-09-17 14:00:00+05	homework
11	5	2	5	4	2024-09-18 09:00:00+05	classwork
12	2	1	5	4	2024-09-19 13:00:00+05	homework
13	1	1	6	3	2024-09-16 14:00:00+05	homework
14	1	1	6	4	2024-09-18 10:00:00+05	classwork
15	2	1	6	3	2024-09-17 09:00:00+05	dictation
16	3	1	6	3	2024-09-19 12:00:00+05	classwork
17	4	2	6	4	2024-09-20 11:00:00+05	classwork
18	2	1	6	3	2024-09-21 10:00:00+05	classwork
19	1	1	7	4	2024-09-15 10:00:00+05	classwork
20	1	1	7	5	2024-09-17 14:00:00+05	homework
21	2	1	7	5	2024-09-16 09:00:00+05	classwork
22	3	1	7	5	2024-09-18 12:00:00+05	classwork
23	5	2	7	5	2024-09-22 09:00:00+05	medium_test
24	7	3	7	4	2024-09-20 13:00:00+05	classwork
25	1	1	8	4	2024-09-16 10:00:00+05	classwork
26	2	1	8	3	2024-09-17 09:00:00+05	dictation
27	2	1	8	4	2024-09-19 14:00:00+05	homework
28	3	1	8	4	2024-09-20 12:00:00+05	classwork
29	4	2	8	4	2024-09-21 11:00:00+05	classwork
30	5	2	8	3	2024-09-22 09:00:00+05	classwork
31	4	3	9	5	2024-09-15 10:00:00+05	classwork
32	4	3	9	5	2024-09-16 14:00:00+05	homework
33	7	3	9	4	2024-09-17 09:00:00+05	classwork
34	8	3	9	4	2024-09-18 13:00:00+05	homework
35	2	1	9	4	2024-09-19 09:00:00+05	dictation
36	2	1	9	5	2024-09-20 14:00:00+05	homework
37	4	3	10	3	2024-09-15 10:00:00+05	classwork
38	4	3	10	4	2024-09-17 14:00:00+05	homework
39	5	2	10	3	2024-09-16 09:00:00+05	classwork
40	5	2	10	4	2024-09-18 13:00:00+05	homework
41	8	3	10	3	2024-09-19 10:00:00+05	classwork
42	2	1	10	4	2024-09-20 15:00:00+05	homework
43	4	3	11	5	2024-09-15 10:00:00+05	classwork
44	4	3	11	5	2024-09-20 10:00:00+05	medium_test
45	7	3	11	5	2024-09-16 12:00:00+05	classwork
46	8	3	11	5	2024-09-17 14:00:00+05	homework
47	2	1	11	4	2024-09-18 09:00:00+05	classwork
48	1	1	11	5	2024-09-19 13:00:00+05	homework
49	4	3	12	4	2024-09-16 10:00:00+05	classwork
50	5	2	12	3	2024-09-17 09:00:00+05	classwork
51	5	2	12	4	2024-09-18 14:00:00+05	homework
52	7	3	12	3	2024-09-19 12:00:00+05	classwork
53	8	3	12	4	2024-09-20 10:00:00+05	classwork
54	1	1	12	4	2024-09-21 11:00:00+05	classwork
55	4	3	13	5	2024-09-15 10:00:00+05	classwork
56	4	3	13	5	2024-09-17 14:00:00+05	homework
57	4	3	13	5	2024-09-25 10:00:00+05	final_test
58	7	3	13	4	2024-09-16 09:00:00+05	classwork
59	2	1	13	5	2024-09-19 09:00:00+05	dictation
60	3	1	13	5	2024-09-20 12:00:00+05	classwork
\.


--
-- Data for Name: parents; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.parents (parent_id, full_name, address, birth_date, gender) FROM stdin;
14	Алексеев Андрей Викторович	г. Москва, ул. Цветочная, д. 3	1985-03-10	m
15	Белова Светлана Викторовна	г. Москва, ул. Лесная, д. 7	1986-07-15	f
16	Волкова Ольга Николаевна	г. Москва, ул. Речная, д. 15	1985-12-20	f
17	Григорьев Дмитрий Петрович	г. Москва, ул. Солнечная, д. 9	1984-09-05	m
18	Денисова Марина Сергеевна	г. Москва, ул. Зелёная, д. 22	1987-04-18	f
19	Емельянова Елена Андреевна	г. Москва, ул. Новая, д. 4	1986-11-12	f
20	Жуков Михаил Дмитриевич	г. Москва, ул. Парковая, д. 11	1983-08-25	m
21	Зайцева Ирина Владимировна	г. Москва, ул. Садовая, д. 6	1985-02-14	f
22	Иванова Татьяна Алексеевна	г. Москва, ул. Молодёжная, д. 18	1984-10-30	f
23	Кузнецов Андрей Сергеевич	г. Москва, ул. Северная, д. 2	1983-06-22	m
\.


--
-- Data for Name: parents_children; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.parents_children (child_id, parent_id, relation_type) FROM stdin;
4	14	father
5	15	mother
6	16	mother
7	17	father
8	18	mother
9	19	mother
10	20	father
11	21	mother
12	22	guardian
13	23	father
\.


--
-- Data for Name: performance_report; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.performance_report (pupil_id, subject_id, mark_total, weights_sum, final_mark) FROM stdin;
4	1	13	3	4
4	2	13	4	3
4	4	14	3	5
5	1	30	6	5
5	3	13	3	4
5	5	8	2	4
5	2	4	1	4
6	1	11	3	4
6	3	6	2	3
6	4	8	2	4
6	2	15	5	3
7	1	13	3	4
7	2	10	2	5
7	3	10	2	5
7	5	20	4	5
7	7	8	2	4
8	1	8	2	4
8	2	13	4	3
8	3	8	2	4
8	4	8	2	4
8	5	6	2	3
9	4	15	3	5
9	7	8	2	4
9	8	4	1	4
9	2	17	4	4
10	4	10	3	3
10	5	10	3	3
10	8	6	2	3
10	2	4	1	4
11	4	30	6	5
11	7	10	2	5
11	8	5	1	5
11	2	8	2	4
11	1	5	1	5
12	4	8	2	4
12	5	10	3	3
12	7	6	2	3
12	8	8	2	4
12	1	8	2	4
13	4	40	8	5
13	7	8	2	4
13	2	15	3	5
13	3	10	2	5
\.


--
-- Data for Name: phone_numbers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.phone_numbers (user_id, phone_number) FROM stdin;
\.


--
-- Data for Name: pupils; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pupils (pupil_id, full_name, address, birth_date, gender) FROM stdin;
4	Алексеев Дмитрий Андреевич	г. Москва, ул. Цветочная, д. 3	2013-05-12	m
5	Белова Анастасия Сергеевна	г. Москва, ул. Лесная, д. 7	2013-08-23	f
6	Волков Максим Игоревич	г. Москва, ул. Речная, д. 15	2013-02-18	m
7	Григорьева Екатерина Дмитриевна	г. Москва, ул. Солнечная, д. 9	2013-11-05	f
8	Денисов Артём Владимирович	г. Москва, ул. Зелёная, д. 22	2013-09-30	m
9	Емельянова София Алексеевна	г. Москва, ул. Новая, д. 4	2013-04-17	f
10	Жуков Тимофей Михайлович	г. Москва, ул. Парковая, д. 11	2013-07-09	m
11	Зайцева Полина Игоревна	г. Москва, ул. Садовая, д. 6	2013-01-25	f
12	Иванов Никита Петрович	г. Москва, ул. Молодёжная, д. 18	2013-10-14	m
13	Кузнецова Варвара Андреевна	г. Москва, ул. Северная, д. 2	2013-06-08	f
\.


--
-- Data for Name: pupils_classes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pupils_classes (pupil_id, class_id, entered_at, left_at) FROM stdin;
4	1	2026-06-12	\N
5	1	2026-06-12	\N
6	1	2026-06-12	\N
7	1	2026-06-12	\N
8	1	2026-06-12	\N
9	2	2026-06-12	\N
10	2	2026-06-12	\N
11	2	2026-06-12	\N
12	2	2026-06-12	\N
13	2	2026-06-12	\N
\.


--
-- Data for Name: responsibilities; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.responsibilities (head_teacher_id, responsibility) FROM stdin;
\.


--
-- Data for Name: schools; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.schools (school_id, title, established_in, address) FROM stdin;
4	Средняя общеобразовательная школа №1	2000	г. Москва, ул. Школьная, д. 1
1	Средняя общеобразовательная школа №1	2000	г. Москва, ул. Школьная, д. 1
\.


--
-- Data for Name: staff; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.staff (worker_id, school_id, hired_at, fired_at) FROM stdin;
1	1	2026-06-12 17:17:46+05	\N
2	1	2026-06-12 17:17:46+05	\N
3	1	2026-06-12 17:17:46+05	\N
\.


--
-- Data for Name: staff_schedule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.staff_schedule (teacher_id, subject_id) FROM stdin;
1	1
1	2
1	3
2	4
2	5
2	6
3	7
3	8
3	4
\.


--
-- Data for Name: subjects; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.subjects (subject_id, title) FROM stdin;
1	Математика
2	Русский язык
3	Литература
4	Английский язык
5	Физика
6	История
7	Биология
8	Химия
\.


--
-- Data for Name: teachers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.teachers (teacher_id, full_name, address, birth_date, gender, head_teacher, emp_rec_book_num) FROM stdin;
1	Иванова Анна Петровна	г. Москва, ул. Учительская, д. 5	1985-03-15	f	t	ТК-000001
2	Петров Сергей Иванович	г. Москва, ул. Научная, д. 12	1980-07-22	m	f	ТК-000002
3	Сидорова Елена Владимировна	г. Москва, ул. Мира, д. 8	1988-11-30	f	t	ТК-000003
\.


--
-- Name: accounts_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.accounts_user_id_seq', 23, true);


--
-- Name: classes_class_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.classes_class_id_seq', 2, true);


--
-- Name: mark_log_mark_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.mark_log_mark_id_seq', 60, true);


--
-- Name: schools_school_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.schools_school_id_seq', 1, true);


--
-- Name: subjects_subject_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.subjects_subject_id_seq', 8, true);


--
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (user_id);


--
-- Name: classes classes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classes
    ADD CONSTRAINT classes_pkey PRIMARY KEY (class_id);


--
-- Name: mark_log mark_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mark_log
    ADD CONSTRAINT mark_log_pkey PRIMARY KEY (mark_id);


--
-- Name: parents_children parents_children_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parents_children
    ADD CONSTRAINT parents_children_pkey PRIMARY KEY (child_id, parent_id);


--
-- Name: parents parents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parents
    ADD CONSTRAINT parents_pkey PRIMARY KEY (parent_id);


--
-- Name: performance_report performance_report_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.performance_report
    ADD CONSTRAINT performance_report_pkey PRIMARY KEY (pupil_id, subject_id);


--
-- Name: phone_numbers phone_numbers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.phone_numbers
    ADD CONSTRAINT phone_numbers_pkey PRIMARY KEY (user_id);


--
-- Name: pupils_classes pupils_classes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pupils_classes
    ADD CONSTRAINT pupils_classes_pkey PRIMARY KEY (pupil_id, class_id, entered_at);


--
-- Name: pupils pupils_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pupils
    ADD CONSTRAINT pupils_pkey PRIMARY KEY (pupil_id);


--
-- Name: responsibilities responsibilities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.responsibilities
    ADD CONSTRAINT responsibilities_pkey PRIMARY KEY (head_teacher_id);


--
-- Name: schools schools_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.schools
    ADD CONSTRAINT schools_pkey PRIMARY KEY (school_id);


--
-- Name: staff staff_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT staff_pkey PRIMARY KEY (worker_id, school_id, hired_at);


--
-- Name: staff_schedule staff_schedule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff_schedule
    ADD CONSTRAINT staff_schedule_pkey PRIMARY KEY (subject_id, teacher_id);


--
-- Name: subjects subjects_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subjects
    ADD CONSTRAINT subjects_pkey PRIMARY KEY (subject_id);


--
-- Name: teachers teachers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teachers
    ADD CONSTRAINT teachers_pkey PRIMARY KEY (teacher_id);


--
-- Name: teachers unique_emp_book; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teachers
    ADD CONSTRAINT unique_emp_book UNIQUE (emp_rec_book_num);


--
-- Name: accounts unique_login; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT unique_login UNIQUE (login);


--
-- Name: phone_numbers unique_phone; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.phone_numbers
    ADD CONSTRAINT unique_phone UNIQUE (phone_number);


--
-- Name: subjects unique_subject_title; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.subjects
    ADD CONSTRAINT unique_subject_title UNIQUE (title);


--
-- Name: phone_numbers trg_format_phone; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_format_phone BEFORE INSERT ON public.phone_numbers FOR EACH ROW EXECUTE FUNCTION public.format_phone();


--
-- Name: mark_log trg_performance_report_after_mark_log; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_performance_report_after_mark_log AFTER INSERT OR DELETE OR UPDATE ON public.mark_log FOR EACH ROW EXECUTE FUNCTION public.trigger_update_performance_report();


--
-- Name: parents_children child_id_fk_for_parents_children; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parents_children
    ADD CONSTRAINT child_id_fk_for_parents_children FOREIGN KEY (child_id) REFERENCES public.pupils(pupil_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: pupils_classes class_id_fk_for_pupils_classes; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pupils_classes
    ADD CONSTRAINT class_id_fk_for_pupils_classes FOREIGN KEY (class_id) REFERENCES public.classes(class_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: classes class_teacher_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classes
    ADD CONSTRAINT class_teacher_id_fk FOREIGN KEY (class_teacher_id) REFERENCES public.teachers(teacher_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: responsibilities head_teacher_id_fk_for_responsibilities; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.responsibilities
    ADD CONSTRAINT head_teacher_id_fk_for_responsibilities FOREIGN KEY (head_teacher_id) REFERENCES public.teachers(teacher_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: parents_children parent_id_fk_for_parents_children; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parents_children
    ADD CONSTRAINT parent_id_fk_for_parents_children FOREIGN KEY (parent_id) REFERENCES public.parents(parent_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: parents parent_user_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.parents
    ADD CONSTRAINT parent_user_id_fk FOREIGN KEY (parent_id) REFERENCES public.accounts(user_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: mark_log pupil_id_fk_for_mark_log; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mark_log
    ADD CONSTRAINT pupil_id_fk_for_mark_log FOREIGN KEY (pupil_id) REFERENCES public.pupils(pupil_id) NOT VALID;


--
-- Name: performance_report pupil_id_fk_for_perf_report; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.performance_report
    ADD CONSTRAINT pupil_id_fk_for_perf_report FOREIGN KEY (pupil_id) REFERENCES public.pupils(pupil_id) NOT VALID;


--
-- Name: pupils_classes pupil_id_fk_for_pupils_classes; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pupils_classes
    ADD CONSTRAINT pupil_id_fk_for_pupils_classes FOREIGN KEY (pupil_id) REFERENCES public.pupils(pupil_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: pupils pupil_user_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pupils
    ADD CONSTRAINT pupil_user_id_fk FOREIGN KEY (pupil_id) REFERENCES public.accounts(user_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: staff school_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT school_id_fk FOREIGN KEY (school_id) REFERENCES public.schools(school_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: classes school_id_fk_for_class; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.classes
    ADD CONSTRAINT school_id_fk_for_class FOREIGN KEY (school_id) REFERENCES public.schools(school_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: mark_log subject_id_fk_for_mark_log; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mark_log
    ADD CONSTRAINT subject_id_fk_for_mark_log FOREIGN KEY (subject_id) REFERENCES public.subjects(subject_id) NOT VALID;


--
-- Name: performance_report subject_id_fk_for_perf_report; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.performance_report
    ADD CONSTRAINT subject_id_fk_for_perf_report FOREIGN KEY (subject_id) REFERENCES public.subjects(subject_id) NOT VALID;


--
-- Name: staff_schedule subjectid_fk_for_staff_schedule; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff_schedule
    ADD CONSTRAINT subjectid_fk_for_staff_schedule FOREIGN KEY (subject_id) REFERENCES public.subjects(subject_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: mark_log teacher_id_fk_for_mark_log; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mark_log
    ADD CONSTRAINT teacher_id_fk_for_mark_log FOREIGN KEY (teacher_id) REFERENCES public.teachers(teacher_id) NOT VALID;


--
-- Name: staff_schedule teacher_id_fk_for_staff_schedule; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff_schedule
    ADD CONSTRAINT teacher_id_fk_for_staff_schedule FOREIGN KEY (teacher_id) REFERENCES public.teachers(teacher_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: teachers teacher_user_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teachers
    ADD CONSTRAINT teacher_user_id_fk FOREIGN KEY (teacher_id) REFERENCES public.accounts(user_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: phone_numbers user_id_fk_for_phones; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.phone_numbers
    ADD CONSTRAINT user_id_fk_for_phones FOREIGN KEY (user_id) REFERENCES public.accounts(user_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- Name: staff worker_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff
    ADD CONSTRAINT worker_id_fk FOREIGN KEY (worker_id) REFERENCES public.teachers(teacher_id) ON UPDATE CASCADE ON DELETE CASCADE NOT VALID;


--
-- PostgreSQL database dump complete
--

\unrestrict zuQZWu1hBSM3iNGYr1LVULyAizXfCMg9Ij2HAWCVV79QUtmhVhoF2sp4U6VaacC

