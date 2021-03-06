from datetime import datetime

from flask import render_template, make_response, redirect, jsonify
from ioos_service_monitor import app, scheduler

from ioos_service_monitor.tasks.regulator import regulate

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

def serialize_date(date):
    if date is not None:
        return date.isoformat()

def serialize_job(job,dt):
    return dict(
        id=job.id,
        scheduled_at=serialize_date(dt),
        created_at=serialize_date(job.created_at),
        enqueued_at=serialize_date(job.enqueued_at),
        ended_at=serialize_date(job.ended_at),
        origin=job.origin,
        result=str(job._result),
        exc_info=job.exc_info,
        description=job.description,
        args=job.args,
        meta=job.meta)

@app.route('/jobs', methods=['GET'])
def jobs():
    jobs = []
    for job,dt in scheduler.get_jobs(with_times=True):
        jobs.append(serialize_job(job,dt))
    return jsonify({ "jobs" : jobs })

@app.route('/regulate', methods=['GET'])
def reg():

    jobs = map(lambda x: x.func, scheduler.get_jobs())

    if regulate not in jobs:
        scheduler.schedule(
            scheduled_time=datetime.now(),  # Time for first execution
            func=regulate,                  # Function to be queued
            interval=300,                   # Time before the function is called again, in seconds
            repeat=None,                    # Repeat this number of times (None means repeat forever)
            result_ttl=600                  # How long to keep the results
        )
        return jsonify({"message" : "regulated"})
    return jsonify({ "message" : "no need to regulate" })

@app.route('/crossdomain.xml', methods=['GET'])
def crossdomain():
    domain = """
    <cross-domain-policy>
        <allow-access-from domain="*"/>
        <site-control permitted-cross-domain-policies="all"/>
        <allow-http-request-headers-from domain="*" headers="*"/>
    </cross-domain-policy>
    """
    response = make_response(domain)
    response.headers["Content-type"] = "text/xml"
    return response

