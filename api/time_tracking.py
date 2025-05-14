from flask import Blueprint, request, jsonify
from models import TimeLog, db
from datetime import datetime

time_tracking_bp = Blueprint('time_tracking', __name__)

@time_tracking_bp.route('/timelogs', methods=['GET'])
def list_timelogs():
    timelogs = TimeLog.query.all()
    return jsonify([t.to_dict() for t in timelogs])

@time_tracking_bp.route('/timelogs', methods=['POST'])
def create_timelog():
    data = request.json
    timelog = TimeLog(
        employee_id=data['employee_id'],
        project_id=data['project_id'],
        task_id=data['task_id'],
        start_time=datetime.fromisoformat(data['start_time']),
        end_time=datetime.fromisoformat(data['end_time'])
    )
    db.session.add(timelog)
    db.session.commit()
    return jsonify(timelog.to_dict()), 201
