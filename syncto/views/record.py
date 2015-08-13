from pyramid.security import NO_PERMISSION_REQUIRED

from cliquet import Service

from syncto.authentication import build_sync_client
from syncto.headers import handle_headers_conversion


record = Service(name='record',
                 description='Firefox Sync Collection Record service',
                 path=('/buckets/syncto/collections/'
                       '{collection_name}/records/{record_id}'),
                 cors_headers=('Last-Modified', 'ETag'))


@record.get(permission=NO_PERMISSION_REQUIRED)
def record_get(request):
    collection_name = request.matchdict['collection_name']
    record_id = request.matchdict['record_id']

    sync_client = build_sync_client(request)
    record = sync_client.get_record(collection_name, record_id)

    record['last_modified'] = int(record.pop('modified') * 1000)

    # Configure headers
    handle_headers_conversion(sync_client.raw_resp, request.response)

    return {'data': record}
