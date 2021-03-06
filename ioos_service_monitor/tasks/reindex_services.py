from datetime import datetime
from urlparse import urlparse

from owslib import fes, csw

from ioos_service_monitor import app,db

from owslib.etree import etree

def reindex_services():
    region_map =    {   'AOOS'      :   '1E96581F-6B73-45AD-9F9F-2CC3FED76EE6',
                        'CENCOOS'   :   'BE483F24-52E7-4DDE-909F-EE8D4FF118EA',
                        'GCOOS'     :   'E77E250D-2D65-463C-B201-535775D222C9',
                        'MARACOOS'  :   'A26F8553-798B-4B1C-8755-1031D752F7C2',
                        'NANOOS'    :   'C6F4754B-30DC-459E-883A-2AC79DA977AB',
                        'NERACOOS'  :   'E13C88D9-3FF3-4232-A379-84B6A1D7083E',
                        'PacIOOS'   :   '78C0463E-2FCE-4AB2-A9C9-6A34BF261F52',
                        'SCOOS'     :   '20A3408F-9EC4-4B36-8E10-BBCDB1E81BDF',
                        'SECOORA'   :   'E796C954-B248-4118-896C-42E6FAA6EDE9' }

    services =      {   'SOS'       :   'urn:x-esri:specification:ServiceType:sos:url',
                        'WMS'       :   'urn:x-esri:specification:ServiceType:wms:url',
                        'WCS'       :   'urn:x-esri:specification:ServiceType:wcs:url',
                        'DAP'       :   'urn:x-esri:specification:ServiceType:odp:url' }

    endpoint = 'http://www.ngdc.noaa.gov/geoportal/csw' # NGDC Geoportal

    c = csw.CatalogueServiceWeb(endpoint, timeout=60)

    with app.app_context():
        for region,uuid in region_map.iteritems():
            # Setup uuid filter
            uuid_filter = fes.PropertyIsEqualTo(propertyname='sys.siteuuid', literal="{%s}" % uuid)

            # Make CSW request
            c.getrecords2([uuid_filter], esn='full')

            for name,record in c.records.iteritems():

                for ref in record.references:
                    
                    # We are only interested in the 'services'
                    if ref["scheme"] in services.values():
                        url = unicode(ref["url"])
                        s =   db.Service.find_one({ 'data_provider' : unicode(region), 'url' : url })
                        if s is None:
                            s               = db.Service()
                            s.url           = url
                            s.data_provider = unicode(region)

                        s.service_id        = unicode(name)
                        s.name              = unicode(record.title)
                        s.service_type      = unicode(next((k for k,v in services.items() if v == ref["scheme"])))
                        s.interval          = 3600 # 1 hour
                        s.tld               = unicode(urlparse(url).netloc)
                        s.updated           = datetime.utcnow()
                        s.save()
                        