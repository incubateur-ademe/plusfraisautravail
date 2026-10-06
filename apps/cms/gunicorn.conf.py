# Gunicorn logging, loaded by entrypoint.sh (`-c`); its CLI flags still win.
# Everything goes to stdout/stderr, which Scaleway ships to Cockpit.

accesslog = "-"
# Client IP from X-Forwarded-For (%(h)s is the Scalingo proxy / Scaleway
# edge), plus %(M)s = response time in ms to spot slow pages.
access_log_format = '%({x-forwarded-for}i)s "%(r)s" %(s)s %(b)s %(M)sms "%(a)s"'


def pre_request(worker, req):
    # The access log line is written after the response: a request that gets
    # the container killed (OOM, failed probe) never shows up there. Log it
    # on the way in too, so the last "start" lines before a restart name it.
    worker.log.info("start %s %s", req.method, req.uri)
