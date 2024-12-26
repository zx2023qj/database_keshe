from flask import Flask, render_template, request, jsonify, session, redirect, url_for,make_response,Blueprint
from app.models import Subject,Choice,Question,Answer,ExamRecord,ExamQuestion,Log,User
from app import db,redis_client
from datetime import datetime, timedelta
import json

exam_blueprint = Blueprint('exam', __name__)

@exam_blueprint.route('/exam', methods=['POST'])
def exam():

    # check if user is student
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    username = session.get('username')
    role = session.get('role')
    if role != 'student':
        return redirect(url_for('index.index'))

    # post request
    if request.method == 'POST':

        # get form data
        subject_name = request.form.get('subject')
        action = request.form.get('action')

        # check if action is start
        if action == 'start':

            # get questions by subejct
            subject = Subject.query.filter_by(name=subject_name).first()
            exam_duration = subject.exam_duration
            subject_usersubjects = subject.subject_usersubjects

            # check if user has done the exam
            for user_subject in subject_usersubjects:
                if user_subject.user.username == username and user_subject.exam_done:
                    return jsonify({'status': 'error', 'message': 'you have done the exam'})
            
            # transport data to front end
            question_data = []

            # get questions in redis with same subject
            redis_questions = redis_client.lrange('questions', 0 ,-1)
            if redis_questions:
                index = 1
                for question in redis_questions:
                    if json.loads(question)['subject'] == subject_name:
                        question_json = json.loads(question)
                        question_json_id = question_json['id']
                        question_json_index = index
                        index = index + 1
                        question_json_title = question_json['title']
                        question_json_description = question_json['description']
                        question_json_type = question_json['type']
                        question_json_difficulty = question_json['difficulty']
                        redis_choices = redis_client.lrange('choices', 0 ,-1)
                        if redis_choices:
                            choices = []
                            for choice in redis_choices:
                                if json.loads(choice)['question_id'] == question_json_id:
                                    choice_json = json.loads(choice)
                                    choices.append({'id': choice_json['id'], 'content': choice_json['content']})
                            question_data.append({'id': question_json_id, 'index': question_json_index, 'title': question_json_title, 'description': question_json_description, 
                            'type': question_json_type, 'difficulty': question_json_difficulty, 'choices': choices})
            
            else:

                # get questions by subject in mysql
                subject_questions = subject.subject_questions
                for index, question in enumerate(subject_questions):
                    choices = Choice.query.filter_by(question_id=question.id).all()
                    question_data.append({'id': question.id,'index':index+1, 'title': question.title, 'description': question.description, 
                    'type': question.type, 'difficulty': question.difficulty, 'choices': [{'id': choice.id, 'content': choice.content} for choice in choices]})
            
            # add exam record
            user_id = User.query.filter_by(username=username).first().id

            # check if exam record exists and update exam record
            exam_record = ExamRecord.query.filter_by(user_id=user_id).first()
            if exam_record:
                exam_record.start_time = datetime.now()+timedelta(hours=8)
                exam_record.end_time = datetime.now()+timedelta(hours=8)
            else:
                exam_record = ExamRecord(user_id=user_id,subject_id=subject.id, score = 0, start_time=datetime.now()+timedelta(hours=8), end_time=datetime.now()+timedelta(hours=8))
                db.session.add(exam_record)
            db.session.commit()

            # exam start log
            exam_start_event = Log(user_id=user_id, action='start', log_type='exam', details = 'start exam of ' + subject_name)
            db.session.add(exam_start_event)
            db.session.commit()
            
            return render_template('exam.html',questions=question_data,duration=exam_duration,subject_name=subject_name)
        elif action == 'submit':

            # get data
            subject = Subject.query.filter_by(name=subject_name).first()
            subject_usersubjects = subject.subject_usersubjects

            # check if user has done the exam
            for user_subject in subject_usersubjects:
                if user_subject.user.username == username and user_subject.exam_done:
                    return jsonify({'status': 'error', 'message': 'you have done the exam'})
            
            # get exam record
            user_id = User.query.filter_by(username=username).first().id
            exam_record = ExamRecord.query.filter_by(user_id=user_id).first()
            exam_score = 0
            
            # get questions by subject
            keys = request.form.keys()
            for key in keys:
                if key == 'subject' or key == 'action':
                    continue

                # get question id and answer
                question_id = key
                question_type = Question.query.filter_by(id=question_id).first().type
                answer = request.form.get(key)

                # check if answer is correct
                is_correct = False
                correct_answer = Answer.query.filter_by(question_id=question_id).first().answer_text
                
                # category answer by question type
                if question_type == 'single_choice':
                    # change answers of chioce question to 'A', 'B', 'C', 'D'
                    answer = chr(int(answer) + 64)
                    # check if answer is correct
                    if answer == correct_answer:
                        is_correct = True
                
                elif question_type == 'multiple_choice':
                    # change answers of chioce question to 'A', 'B', 'C', 'D'
                    answer = answer.split(',')
                    answer = [chr(int(a) + 64) for a in answer]
                    answer = ','.join(answer)
                    # check if answer is correct
                    if answer == correct_answer:
                        is_correct = True
                
                elif question_type == 'true_false' or question_type == 'fill_in_the_blank':
                    # check if answer is correct
                    if answer == correct_answer:
                        is_correct = True
                
                # add exam score
                if is_correct:
                    exam_score += 1
                
                # add exam question
                exam_question = ExamQuestion(exam_record_id=exam_record.id, question_id=question_id, user_answer=answer, is_correct=is_correct)
                db.session.add(exam_question)
                db.session.commit()

            # update exam record
            exam_record.score = exam_score
            exam_record.end_time = datetime.now()+timedelta(hours=8)
            db.session.commit()

            # update user subject
            for user_subject in subject_usersubjects:
                user_subject.exam_done = True
                db.session.commit()

            # exam submit log
            exam_submit_event = Log(user_id=user_id, action='submit', log_type='exam', details = 'submit exam of ' + subject_name)
            db.session.add(exam_submit_event)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'exam submitted'})
            
    return jsonify({'status': 'error', 'message': 'permission denied'})