from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core_hr.models import BiometricDevice
from profile_api.views import _process_event  # reuse logic
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    # Optional dependency: python-zk (ZKTeco SDK wrapper)
    # pip install zk (ask for permission before installing)
    from zk import ZK, const
    HAS_ZK = True
except Exception:  # pragma: no cover
    ZK = None
    const = None
    HAS_ZK = False


class Command(BaseCommand):
    help = "Poll ZKTeco devices over LAN and ingest attendance since last pull."

    def add_arguments(self, parser):
        parser.add_argument('--device-id', type=int, help='Specific device ID to poll; otherwise all active devices with IP configured')
        parser.add_argument('--since-minutes', type=int, default=1440, help='Fallback window if last_pull is empty')

    def handle(self, *args, **options):
        if not HAS_ZK:
            self.stdout.write(self.style.WARNING('python-zk library not installed. Install with `pip install zk` (requires approval)'))
        qs = BiometricDevice.objects.filter(is_active=True).exclude(ip_address=None)
        if options.get('device_id'):
            qs = qs.filter(id=options['device_id'])
        count = 0
        for d in qs:
            if not d.ip_address:
                continue
            if not HAS_ZK:
                logger.warning("Skipping device %s (%s): python-zk not installed", d.name, d.ip_address)
                continue
            try:
                self.stdout.write(f"Connecting to {d.name} {d.ip_address}:{d.port} ...")
                try:
                    password = int(getattr(d, 'comm_key', 0) or 0)
                    zk = ZK(d.ip_address, port=d.port, timeout=10, password=password, force_udp=False, ommit_ping=False)
                    conn = zk.connect()
                except Exception:
                    # Fallback to UDP transport for devices that do not accept TCP SDK
                    self.stdout.write(self.style.WARNING("TCP connect failed; retrying with UDP..."))
                    password = int(getattr(d, 'comm_key', 0) or 0)
                    zk = ZK(d.ip_address, port=d.port, timeout=10, password=password, force_udp=True, ommit_ping=False)
                    conn = zk.connect()
                try:
                    # get attendance logs
                    records = conn.get_attendance()
                    if not records:
                        self.stdout.write("No logs found")
                        conn.disconnect()
                        continue
                    # Use last_pull to limit processing window
                    last_pull = d.last_pull or (timezone.now() - timezone.timedelta(minutes=options['since_minutes']))
                    for r in records:
                        # r.user_id, r.timestamp, r.status (0=in, 1=out on some firmwares)
                        ts = r.timestamp
                        if ts.tzinfo is None:
                            ts = timezone.make_aware(ts)
                        if ts < last_pull:
                            continue
                        event_type = 'checkin' if getattr(r, 'punch', getattr(r, 'status', 0)) in (0, 4) else 'checkout'
                        _process_event(d.company, d, str(r.user_id), event_type, ts, raw_payload={'source': 'poll', 'raw': str(r)})
                        count += 1
                    d.last_pull = timezone.now()
                    d.save(update_fields=['last_pull'])
                finally:
                    try:
                        conn.disconnect()
                    except Exception:
                        pass
            except Exception as e:  # pragma: no cover
                logger.exception("Failed polling device %s: %s", d.id, e)
        self.stdout.write(self.style.SUCCESS(f"Polling completed. Ingested events: {count}"))

