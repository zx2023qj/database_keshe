from flask import Flask, render_template, request, jsonify, session, redirect, url_for,make_response,Blueprint
from app.models import User,Subject,Question,Log,Answer,Choice
from app import db,redis_client
from datetime import datetime, timedelta
import json

question_blueprint = Blueprint('question', __name__)

# question routes
@question_blueprint.route('/question', methods=['POST'])
def question():

    # check if user is logged in
    username = session.get('username')
    if not username:
        return jsonify({'status': 'error', 'message': 'Please login first'})
    
    # check if user is student
    role = session.get('role')
    if role == 'student':
        return jsonify({'status': 'error', 'message': 'Permission denied'})

    user = User.query.filter_by(username=username).first()
    user_id = user.id

    # check if user is teacher
    if role == 'teacher':
        user_subjects = user.user_usersubjects
        user_subjects_names = [user_subject.subject.name for user_subject in user_subjects]
    
    action = request.form.get('action')
    if action == 'read':

        # teacher can only read part of subject questions
        if role == 'teacher':

            # get user subjects
            user_subjects = user.user_usersubjects
            subjects = [user_subject.subject for user_subject in user_subjects]

            # get questions
            question_data = []

            # read questions from redis
            redis_questions = redis_client.lrange('questions', 0, -1)
            user_subjects_names = [subject.name for subject in subjects]
            if redis_questions:
                for redis_question in redis_questions:
                    redis_question = json.loads(redis_question)
                    if redis_question['subject'] in user_subjects_names:
                        question_data.append(redis_question)

            # read questions from mysql
            else:
                subjects_questions = [subject.subject_questions for subject in subjects]
                question_data = []
                for subject_questions in subjects_questions:
                    [question_data.append({'id': question.id, 'title': question.title,'type': question.type, 'difficulty': question.difficulty, 'subject': question.subject.name, 'creator': User.query.filter(User.id == question.creator_id).first().username}) for question in subject_questions]

        
        # admin can read all questions
        elif role == 'admin':

            # read questions from redis
            redis_questions = redis_client.lrange('questions', 0, -1)
            if redis_questions:
                question_data = [json.loads(redis_question) for redis_question in redis_questions]
            else:
            
            # read questions from mysql
                read_questions = Question.query.all()
                question_data = [{'id': question.id, 'title': question.title,'type': question.type, 'difficulty': question.difficulty, 'subject': question.subject.name, 'creator': User.query.filter(User.id == question.creator_id).first().username} for question in read_questions]
        
        # read question log
        question_read_event = Log(user_id=user_id, action='read',log_type='question',details='Read questions')
        db.session.add(question_read_event)
        db.session.commit()
        return jsonify({'question': question_data})

    elif action == 'add':

        # get data from form
        question_title = request.form.get('question')
        add_question = Question.query.filter(Question.title == question_title).first()

        # check if question already exists
        if add_question:
            return jsonify({'status': 'error', 'message': 'Question already exists'})
        question_subject = request.form.get('subject')

        # check if teacher has the subject
        if role == 'teacher':
            if question_subject not in user_subjects_names:
                return jsonify({'status': 'error', 'message': 'error subject'})

        add_subject = Subject.query.filter(Subject.name == question_subject).first()
        # check if subject not exists
        if not add_subject:
            return jsonify({'status': 'error', 'message': 'Subject not exists'})

        # get data from form
        question_description = request.form.get('description')
        question_type = request.form.get('type')
        question_difficulty = request.form.get('difficulty')

        if question_type == 'single_choice':
            add_question_options = request.form.getlist('options[]')
            add_question_answer = request.form.get('correct_answer')

            # check if the answer is fit for single choice
            add_question_answer_array = add_question_answer.split(',')
            if len(add_question_answer_array) != 1:
                return jsonify({'status': 'error', 'message': 'Single choice question should have only one answer'})
            
            # check if the answer is in the options
            for answer in add_question_answer_array:
                if answer not in ['A', 'B', 'C', 'D']:
                    return jsonify({'status': 'error', 'message': 'Answer should be in the options or Check if the answer is formatted correctly'})
            
            # add question
            add_question = Question(title=question_title, description=question_description, type=question_type, difficulty=question_difficulty, subject_id=add_subject.id, creator_id=user_id)
            db.session.add(add_question)
            db.session.commit()

            # add question to redis
            question_data = {'id': add_question.id, 'title': add_question.title,'description':add_question.description,'type': add_question.type, 'difficulty': add_question.difficulty, 'subject': question_subject, 'creator': username}
            redis_client.rpush('questions',json.dumps(question_data))

            # add question log
            question_add_event = Log(user_id=user_id, action='add',log_type='question',details='Add question:' + question_title)
            db.session.add(question_add_event)
            db.session.commit()

            # add choices
            for index, option in enumerate(add_question_options):
                is_correct = True if chr(65 + index) in add_question_answer_array else False
                add_choice = Choice(question_id=add_question.id, content=option, is_correct=is_correct)
                db.session.add(add_choice)
                db.session.commit()

                # add choice to redis
                choice_data = {'id': add_choice.id, 'question_id': add_choice.question_id,'content':add_choice.content,'is_correct': add_choice.is_correct}
                redis_client.rpush('choices',json.dumps(choice_data))

            
            # add choice log
            choice_add_event = Log(user_id=user_id, action='add',log_type='choice',details='Add choices for question:' + question_title)
            db.session.add(choice_add_event)
            db.session.commit()

            # add answer
            add_answer = Answer(question_id=add_question.id, answer_text=add_question_answer)
            db.session.add(add_answer)
            db.session.commit()

            # add answer log
            answer_add_event = Log(user_id=user_id, action='add',log_type='answer',details='Add answer for question:' + question_title)
            db.session.add(answer_add_event)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Question added successfully'})
        
        elif question_type == 'multiple_choice':
            add_question_options = request.form.getlist('options[]')
            add_question_answer = request.form.get('correct_answer')
            add_question_answer_array = add_question_answer.split(',')
            
            # check if the answer is fit for multiple choice
            if len(add_question_answer_array) < 2:
                return jsonify({'status': 'error', 'message': 'Multiple choice question should have at least two answers'})
            
            # check if the answer is in the options
            for answer in add_question_answer_array:
                if answer not in ['A', 'B', 'C', 'D']:
                    return jsonify({'status': 'error', 'message': 'Answer should be in the options or Check if the answer is formatted correctly'})
        
            # remove duplicate answers
            unique_answers = set(add_question_answer_array)

            # sort answers
            sorted_answers = sorted(unique_answers)

            # join answers
            add_question_answer = ','.join(sorted_answers)

            # add question
            add_question = Question(title=question_title, description=question_description, type=question_type, difficulty=question_difficulty, subject_id=add_subject.id, creator_id=user_id)
            db.session.add(add_question)
            db.session.commit()
            
            # add question to redis
            question_data = {'id': add_question.id, 'title': add_question.title,'description':add_question.description,'type': add_question.type, 'difficulty': add_question.difficulty, 'subject': add_subject.name, 'creator': username}
            redis_client.rpush('questions',json.dumps(question_data))

            # add question log
            question_add_event = Log(user_id=user_id, action='add',log_type='question',details='Add question:' + question_title)
            db.session.add(question_add_event)
            db.session.commit()

            # add choices
            for index, option in enumerate(add_question_options):
                is_correct = True if chr(65 + index) in add_question_answer else False
                add_choice = Choice(question_id=add_question.id, content=option, is_correct=is_correct)
                db.session.add(add_choice)
                db.session.commit()
                # add choice to redis
                choice_data = {'id': add_choice.id, 'question_id': add_choice.question_id,'content':add_choice.content,'is_correct': add_choice.is_correct}
                redis_client.rpush('choices',json.dumps(choice_data))

            # add choice log
            choice_add_event = Log(user_id=user_id, action='add',log_type='choice',details='Add choices for question:' + question_title)
            db.session.add(choice_add_event)
            db.session.commit()

            # add answer
            add_answer = Answer(question_id=add_question.id, answer_text=add_question_answer)
            db.session.add(add_answer)
            db.session.commit()

            # add answer log
            answer_add_event = Log(user_id=user_id, action='add',log_type='answer',details='Add answer for question:' + question_title)
            db.session.add(answer_add_event)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Question added successfully'})

        elif question_type == 'true_false':
            add_question_answer = request.form.get('correct_answer')

            # check if the answer is fit for true false
            if add_question_answer not in ['true', 'false']:
                return jsonify({'status': 'error', 'message': 'Answer should be True or False'})
            
            # add question
            add_question = Question(title=question_title, description=question_description, type=question_type, difficulty=question_difficulty, subject_id=add_subject.id, creator_id=user_id)
            db.session.add(add_question)
            db.session.commit()
            
            # add question to redis
            question_data = {'id': add_question.id, 'title': add_question.title,'description':add_question.description,'type': add_question.type, 'difficulty': add_question.difficulty, 'subject': question_subject, 'creator': username}
            redis_client.rpush('questions',json.dumps(question_data))

            # add question log
            question_add_event = Log(user_id=user_id, action='add',log_type='question',details='Add question:' + question_title)
            db.session.add(question_add_event)
            db.session.commit()
            
            # add answer
            add_answer = Answer(question_id=add_question.id, answer_text=add_question_answer)
            db.session.add(add_answer)
            db.session.commit()
            
            # add answer log
            answer_add_event = Log(user_id=user_id, action='add',log_type='answer',details='Add answer for question:' + question_title)
            db.session.add(answer_add_event)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Question added successfully'})

        elif question_type == 'fill_in_the_blank':
            add_question_answer = request.form.get('correct_answer')

            # add question
            add_question = Question(title=question_title, description=question_description, type=question_type, difficulty=question_difficulty, subject_id=add_subject.id, creator_id=user_id)
            db.session.add(add_question)
            db.session.commit()

            # add question to redis
            question_data = {'id': add_question.id, 'title': add_question.title,'description':add_question.description,'type': add_question.type, 'difficulty': add_question.difficulty, 'subject': question_subject, 'creator': username}
            redis_client.rpush('questions',json.dumps(question_data))

            # add question log
            question_add_event = Log(user_id=user_id, action='add',log_type='question',details='Add question:' + question_title)
            db.session.add(question_add_event)
            db.session.commit()

            # add answer
            add_answer = Answer(question_id=add_question.id, answer_text=add_question_answer)
            db.session.add(add_answer)
            db.session.commit()

            # add answer log
            answer_add_event = Log(user_id=user_id, action='add',log_type='answer',details='Add answer for question:' + question_title)
            db.session.add(answer_add_event)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Question added successfully'})

        else:
            return jsonify({'status': 'error', 'message': 'submit error'})

    elif action == 'edit':
        question_title = request.form.get('question')
        edit_question = Question.query.filter(Question.title == question_title).first()

        # check if question not exists
        if not edit_question:
            return jsonify({'status': 'error', 'message': 'Question not exists'})
        question_subject = request.form.get('subject')

        # check teacher
        if role == 'teacher':

            # check if teacher has the subject
            if question_subject not in user_subjects_names:
                return jsonify({'status': 'error', 'message': 'error subject'})
            
            # check if teacher was the creator
            if edit_question.creator_id != user_id:
                return jsonify({'status': 'error', 'message': 'You are not the creator of the question'})

        # check if subject is fit for the question's subject
        edit_subject = Subject.query.filter(Subject.name == question_subject).first()
        if not edit_subject:
            return jsonify({'status': 'error', 'message': 'Subject not exists'})
        if edit_question.subject_id != edit_subject.id:
            return jsonify({'status': 'error', 'message': 'Subject not fit for the question'})

        # check if type is fit for the question's type
        question_type = request.form.get('type')
        if edit_question.type != question_type:
            return jsonify({'status': 'error', 'message': 'Type not fit for the question'})

        # edit question
        question_description = request.form.get('description')
        question_difficulty = request.form.get('difficulty')
        edit_question.description = question_description
        edit_question.difficulty = question_difficulty
        update_time = datetime.utcnow() + timedelta(hours=8)
        edit_question.updated_time = update_time

        # edit question in redis
        question_data = {'id': edit_question.id, 'title': edit_question.title,'description':edit_question.description,'type': edit_question.type, 'difficulty': edit_question.difficulty, 'subject': question_subject, 'creator': username}
        redis_questions = redis_client.lrange('questions', 0, -1)
        for index, redis_question in enumerate(redis_questions):
            redis_question = json.loads(redis_question)
            if redis_question['id'] == edit_question.id:
                redis_client.lset('questions', index, json.dumps(question_data))
                break    

        if question_type == 'single_choice':
            edit_question_options = request.form.getlist('options[]')
            edit_question_answer = request.form.get('correct_answer')

            # check if the answer is fit for single choice
            edit_question_answer_array = edit_question_answer.split(',')
            if len(edit_question_answer_array) != 1:
                return jsonify({'status': 'error', 'message': 'Single choice question should have only one answer'})
            
            # check if the answer is in the options
            for answer in edit_question_answer_array:
                if answer not in ['A', 'B', 'C', 'D']:
                    return jsonify({'status': 'error', 'message': 'Answer should be in the options or Check if the answer is formatted correctly'})
            
            # edit choices
            edit_choices = Choice.query.filter(Choice.question_id == edit_question.id).all()
            for index, option in enumerate(edit_question_options):
                is_correct = True if chr(65 + index) in edit_question_answer_array else False
                edit_choices[index].content = option
                edit_choices[index].is_correct = is_correct
                update_time = datetime.utcnow() + timedelta(hours=8)
                edit_choices[index].updated_time = update_time
                db.session.commit()
                # edit choice in redis
                choice_data = {'id': edit_choices[index].id, 'question_id': edit_choices[index].question_id,'content':edit_choices[index].content,'is_correct': edit_choices[index].is_correct}
                redis_choices = redis_client.lrange('choices', 0, -1)
                for redis_index, redis_choice in enumerate(redis_choices):
                    redis_choice = json.loads(redis_choice)
                    if redis_choice['id'] == edit_choices[index].id:
                        redis_client.lset('choices', redis_index, json.dumps(choice_data))
                        break
            
            # edit answer
            edit_answer = Answer.query.filter(Answer.question_id == edit_question.id).first()
            edit_answer.answer_text = edit_question_answer
            update_time = datetime.utcnow() + timedelta(hours=8)
            edit_answer.updated_time = update_time
            db.session.commit()

            # edit question log , choice log and answer log
            question_edit_event = Log(user_id=user_id, action='edit',log_type='question',details='Edit question:' + question_title)
            db.session.add(question_edit_event)
            choice_edit_event = Log(user_id=user_id, action='edit',log_type='choice',details='Edit choices for question:' + question_title)
            db.session.add(choice_edit_event)
            answer_edit_event = Log(user_id=user_id, action='edit',log_type='answer',details='Edit answer for question:' + question_title)
            db.session.add(answer_edit_event)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Question edited successfully'})

        elif question_type == 'multiple_choice':
            edit_question_options = request.form.getlist('options[]')
            edit_question_answer = request.form.get('correct_answer')
            edit_question_answer_array = edit_question_answer.split(',')
            # check if the answer is fit for multiple choice
            if len(edit_question_answer_array) < 2:
                return jsonify({'status': 'error', 'message': 'Multiple choice question should have at least two answers'})
            
            # check if the answer is in the options
            for answer in edit_question_answer_array:
                if answer not in ['A', 'B', 'C', 'D']:
                    return jsonify({'status': 'error', 'message': 'Answer should be in the options or Check if the answer is formatted correctly'})
            
            # remove duplicate answers
            unique_answers = set(add_question_answer_array)

            # sort answers
            sorted_answers = sorted(unique_answers)

            # join answers
            add_question_answer = ','.join(sorted_answers)

            # edit choices
            edit_choices = Choice.query.filter(Choice.question_id == edit_question.id).all()
            for index, option in enumerate(edit_question_options):
                is_correct = True if chr(65 + index) in edit_question_answer else False
                edit_choices[index].content = option
                edit_choices[index].is_correct = is_correct
                update_time = datetime.utcnow() + timedelta(hours=8)
                edit_choices[index].updated_time = update_time
                db.session.commit()
                # edit choice in redis
                choice_data = {'id': edit_choices[index].id, 'question_id': edit_choices[index].question_id,'content':edit_choices[index].content,'is_correct': edit_choices[index].is_correct}
                redis_choices = redis_client.lrange('choices', 0, -1)
                for redis_index, redis_choice in enumerate(redis_choices):
                    redis_choice = json.loads(redis_choice)
                    if redis_choice['id'] == edit_choices[index].id:
                        redis_client.lset('choices', redis_index, json.dumps(choice_data))
                        break

            # edit answer
            edit_answer = Answer.query.filter(Answer.question_id == edit_question.id).first()
            edit_answer.answer_text = edit_question_answer
            update_time = datetime.utcnow() + timedelta(hours=8)
            edit_answer.updated_time = update_time
            db.session.commit()

            # edit question log , choice log and answer log
            question_edit_event = Log(user_id=user_id, action='edit',log_type='question',details='Edit question:' + question_title)
            db.session.add(question_edit_event)
            choice_edit_event = Log(user_id=user_id, action='edit',log_type='choice',details='Edit choices for question:' + question_title)
            db.session.add(choice_edit_event)
            answer_edit_event = Log(user_id=user_id, action='edit',log_type='answer',details='Edit answer for question:' + question_title)
            db.session.add(answer_edit_event)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Question edited successfully'})
        
        elif question_type == 'true_false':
            edit_question_answer = request.form.get('correct_answer')

            # check if the answer is fit for true false
            if edit_question_answer not in ['true', 'false']:
                return jsonify({'status': 'error', 'message': 'Answer should be True or False'})

            # edit answer
            edit_answer = Answer.query.filter(Answer.question_id == edit_question.id).first()
            edit_answer.answer_text = edit_question_answer
            update_time = datetime.utcnow() + timedelta(hours=8)
            edit_answer.updated_time = update_time
            db.session.commit()

            # edit question log and answer log
            question_edit_event = Log(user_id=user_id, action='edit',log_type='question',details='Edit question:' + question_title)
            db.session.add(question_edit_event)
            answer_edit_event = Log(user_id=user_id, action='edit',log_type='answer',details='Edit answer for question:' + question_title)
            db.session.add(answer_edit_event)
            db.session.commit()

            return jsonify({'status': 'success', 'message': 'Question edited successfully'})

        elif question_type == 'fill_in_the_blank':
            edit_question_answer = request.form.get('correct_answer')
            
            # edit answer
            edit_answer = Answer.query.filter(Answer.question_id == edit_question.id).first()
            edit_answer.answer_text = edit_question_answer
            update_time = datetime.utcnow() + timedelta(hours=8)
            edit_answer.updated_time = update_time
            db.session.commit()

            # edit question log and answer log
            question_edit_event = Log(user_id=user_id, action='edit',log_type='question',details='Edit question:' + question_title)
            db.session.add(question_edit_event)
            answer_edit_event = Log(user_id=user_id, action='edit',log_type='answer',details='Edit answer for question:' + question_title)
            db.session.add(answer_edit_event)
            db.session.commit()

            return jsonify({'status': 'success', 'message': 'Question edited successfully'})

        else:
            return jsonify({'status': 'error', 'message': 'submit error'})

    elif action == 'delete':
        question_title = request.form.get('question')
        delete_question = Question.query.filter(Question.title == question_title).first()
        
        # check if question not exists
        if not delete_question:
            return jsonify({'status': 'error', 'message': 'Question not exists'})
        
        # check teacher
        if role == 'teacher':
            # check if teacher was the creator
            if delete_question.creator_id != user_id:
                return jsonify({'status': 'error', 'message': 'You are not the creator of the question'})

        # delete question in redis
        redis_questions = redis_client.lrange('questions', 0, -1)
        for index, redis_question in enumerate(redis_questions):
            redis_question = json.loads(redis_question)
            if redis_question['id'] == delete_question.id:
                redis_client.lrem('questions', 0, json.dumps(redis_question))
        
        # delete choices in redis
        redis_choices = redis_client.lrange('choices', 0, -1)
        for redis_choice in redis_choices:
            redis_choice = json.loads(redis_choice)
            if redis_choice['question_id'] == delete_question.id:
                redis_client.lrem('choices', 0, json.dumps(redis_choice))

        # delete question
        db.session.delete(delete_question)
        db.session.commit()
        
        # delete question log
        question_delete_event = Log(user_id=user_id, action='delete',log_type='question',details='Delete question:' + question_title)
        db.session.add(question_delete_event)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Question deleted successfully'})

    return jsonify({'status': 'error', 'message': 'Invalid action'})