import json
import base64
from datetime import datetime, date, time

import requests
import pytz
import authentication

"""Visegrad+ parliament API client module.
Contains functions to make API requests easily.
"""

__all__ = [
	'parliament', 'authorize', 'deauthorize',
	'get', 'getall', 'getfirst', 'post', 'put', 'patch', 'delete',
	'timezone', 'utc_to_local', 'local_to_utc',
]

SERVER_NAME = 'api.parldata.eu'
#SERVER_NAME = '127.0.0.1:5000'
SERVER_CERT = 'server_cert_prod.pem'
SERVER_CERT = 'server_cert.pem'
PARLIAMENT = ''
PAYLOAD_HEADERS = {
	'Content-Type': 'application/json',
}

def _endpoint(resource, method):
	"""Returns URL of the given resource and method.
	http:// is used for GET method while https:// for the others.
	http:// is used for all methods on localhost.
	"""
	if method=='GET' or SERVER_NAME.startswith('localhost:') or SERVER_NAME.startswith('127.0.0.1:'):
		protocol = 'http'
	else:
		protocol = 'https'
	if PARLIAMENT:
		url = '%s://%s/%s/%s' % (protocol, SERVER_NAME, PARLIAMENT, resource)
	else:
		url = '%s://%s/%s' % (protocol, SERVER_NAME, resource)
	return url


def _jsonify_dict_values(params):
	"""Returns `params` dictionary with all values of type dictionary
	or list serialized to JSON. This is necessary for _requests_
	library to pass parameters in the query string correctly.
	"""
	return { k: json.dumps(v)	if isinstance(v, dict) or isinstance(v, list) else v
		for k, v in params.items()
	}


def parliament(parl):
	"""Sets the parliament the following requests will be sent to."""
	global PARLIAMENT
	PARLIAMENT = parl


def authorize(username, password):
	"""Sets API username and password for the following data modifying
	requests.
	"""
	s = '%s:%s' % (username, password)
	PAYLOAD_HEADERS['Authorization'] = b'Basic ' + base64.b64encode(s.encode('ascii'))


def deauthorize():
	"""Unsets API username and password - the following data modifying
	requests will be anonymous.
	"""
	PAYLOAD_HEADERS.pop('Authorization', None)


def get(resource, **kwargs):
	"""Makes a GET (read) request to the API.
	Lookup parameters are specified as keyword arguments.
	"""
	#print(_endpoint(resource, 'GET'))
	resp = requests.get(
		_endpoint(resource, 'GET'),
		params=_jsonify_dict_values(kwargs),
		verify=SERVER_CERT
	)
	resp.raise_for_status()
	return resp.json()

def getall(resource, **kwargs):
    """Generator that generates sequence of all found results without paging.
    Lookup parameters are specified as keyword arguments.
    Usage:
    items = vpapi.getall(resource, where={...})
    for i in items:
    ...
    """
    page = 1
    while True:
        resp = get(resource, page=page, **kwargs)
        for item in resp['_items']:
            yield item
        if 'next' not in resp['_links']: 
            break
        page += 1

def post(resource, data, **kwargs):
	"""Makes a POST (create) request to the API.
	`data` contains dictionary with data of the entity(ies) to create
	and eventual parameters may be specified as keyword arguments.
	"""
	#print(_endpoint(resource,'POST'))
	resp = requests.post(
		_endpoint(resource, 'POST'),
		params=_jsonify_dict_values(kwargs),
		data=json.dumps(data),
		headers=PAYLOAD_HEADERS,
		verify=SERVER_CERT
	)
	resp.raise_for_status()
	return resp.json()


def put(resource, data, **kwargs):
	"""Makes a PUT (replace) request to the API.
	`data` contains dictionary with data of the replacing entity and
	eventual parameters may be specified as keyword arguments.
	"""
	resp = requests.put(
		_endpoint(resource, 'PUT'),
		params=_jsonify_dict_values(kwargs),
		data=json.dumps(data),
		headers=PAYLOAD_HEADERS,
		verify=SERVER_CERT
	)
	resp.raise_for_status()
	return resp.json()


def patch(resource, data, **kwargs):
	"""Makes a PATCH (update) request to the API.
	`data` contains dictionary with fields to update and their values,
	eventual parameters may be specified as keyword arguments.
	"""
	resp = requests.patch(
		_endpoint(resource, 'PATCH'),
		params=_jsonify_dict_values(kwargs),
		data=json.dumps(data),
		headers=PAYLOAD_HEADERS,
		verify=SERVER_CERT
	)
	resp.raise_for_status()
	return resp.json()


def delete(resource):
	"""Makes a DELETE request to the API."""
	resp = requests.delete(
		_endpoint(resource, 'DELETE'),
		headers=PAYLOAD_HEADERS,
		verify=SERVER_CERT
	)
	resp.raise_for_status()
	return {}

def timezone(name):
	"""Sets the local timezone to be used by `utc_to_local()` and
	`local_to_utc()` helper functions.
	"""
	global LOCAL_TIMEZONE
	LOCAL_TIMEZONE = pytz.timezone(name)


def utc_to_local(val, to_string=None):
	"""Converts datetime or its string representation in ISO 8601 format
	from UTC time returned by API to local time. The local timezone must
	be previously set by `vpapi.timezone()` function.

	Returns the result in the same type as input if `to_string` is not
	given. String output or datetime output can be enforced by setting
	`to_string` to True or False respectively.
	"""
	if LOCAL_TIMEZONE is None:
		raise ValueError('The local timezone must be set first, use vpapi.timezone()')
	format = '%Y-%m-%dT%H:%M:%S'
	out = datetime.strptime(val, format) if isinstance(val, str) else val
	if not isinstance(out, datetime):
		raise TypeError('Only datetime object or ISO 8601 string can be converted')

	out = pytz.utc.localize(out)
	out = out.astimezone(LOCAL_TIMEZONE)

	if to_string or to_string is None and isinstance(val, str):
		return out.strftime(format)
	else:
		return out


def local_to_utc(val, to_string=True):
	"""Converts datetime or its string representation in ISO 8601 format
	from local time to UTC time required by API. The local timezone must
	be previously set by `vpapi.timezone()` function.

	Returns the result in the same type as input if `to_string` is not
	given. String output or datetime output can be enforced by setting
	`to_string` to True or False respectively.
	"""
	if LOCAL_TIMEZONE is None:
		raise ValueError('The local timezone must be set first, use vpapi.timezone()')
	format = '%Y-%m-%dT%H:%M:%S'
	out = datetime.strptime(val, format) if isinstance(val, str) else val
	if not isinstance(out, datetime):
		raise TypeError('Only datetime object or ISO 8601 string can be converted')

	out = LOCAL_TIMEZONE.localize(out)
	out = out.astimezone(pytz.utc)

	if to_string or to_string is None and isinstance(val, str):
		return out.strftime(format)
	else:
		return out
