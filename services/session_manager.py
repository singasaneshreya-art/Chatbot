from flask import session

def get_history():
    if 'history' not in session:
        session['history'] = []
    return session['history']

def add_message(role, content):
    history = get_history()
    cleaned_role = 'user' if role == 'user' else 'assistant'
    history.append({'role': cleaned_role, 'content': content})
    session['history'] = history
    session.modified = True

def clear_history():
    session['history'] = []
    session['flow'] = None
    session['active_order_id'] = None
    session.modified = True

def set_flow(flow_name):
    session['flow'] = flow_name
    session.modified = True

def get_flow():
    return session.get('flow')

def set_active_order_id(order_id):
    session['active_order_id'] = order_id
    session.modified = True

def get_active_order_id():
    return session.get('active_order_id')

def set_user_name(name):
    session['user_name'] = name
    session.modified = True

def get_user_name():
    return session.get('user_name')

def set_user_email(email):
    session['user_email'] = email
    session.modified = True

def get_user_email():
    return session.get('user_email')

def set_pre_collect_flow(flow):
    session['pre_collect_flow'] = flow
    session.modified = True

def get_pre_collect_flow():
    return session.get('pre_collect_flow')

def clear_collect_state():
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('pre_collect_flow', None)
    if session.get('flow') in ['collecting_name', 'collecting_email']:
        session['flow'] = None
    session.modified = True

