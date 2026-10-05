import warnings

from testprotocols.models import (
    AppFlow,
    Connection,
    DnsRecord,
    QoEResult,
    RadiusAccountingRecord,
    RadiusUser,
    RuleProtocol,
    WifiBand,
    WifiStation,
)


def test_device_vocabularies_store_as_given() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        conn = Connection(
            protocol=RuleProtocol.TCP,
            src_ip="192.0.2.1",
            dst_ip="192.0.2.2",
            src_port=1,
            dst_port=2,
            state="ESTABLISHED",
            timeout_seconds=1,
            bytes_orig=0,
            bytes_reply=0,
            packets_orig=0,
            packets_reply=0,
        )
        record = DnsRecord(
            name="example.org.", record_type="CAA", ttl=60, data='0 issue "ca.example"'
        )
        qoe = QoEResult(protocol="http/1.0")
        user = RadiusUser(username="u", eap_methods=["PEAP-MSCHAPv2", "EAP-FAST"])
        acct = RadiusAccountingRecord(
            timestamp=0.0,
            session_id="s",
            username="u",
            nas_address="192.0.2.3",
            record_type="Start",
            session_time=None,
            input_octets=None,
            output_octets=None,
            input_packets=None,
            output_packets=None,
            terminate_cause="Vendor-Cause",
        )
        flow = AppFlow(
            application="app",
            category="gaming",
            src_ip="192.0.2.1",
            dst_ip="192.0.2.2",
            wan_interface="wan1",
            bytes_sent=0,
            bytes_received=0,
        )
        flow_unknown = AppFlow(
            application="app",
            category="vendor-category",
            src_ip="192.0.2.1",
            dst_ip="192.0.2.2",
            wan_interface="wan1",
            bytes_sent=0,
            bytes_received=0,
        )
        station = WifiStation(
            mac="02:00:00:00:00:01",
            bss_name="bss",
            band=WifiBand.GHZ_5,
            ip_address=None,
            associated_since=0.0,
            rssi_dbm=-50,
            snr_db=None,
            tx_rate_mbps=1.0,
            rx_rate_mbps=1.0,
            tx_bytes=0,
            rx_bytes=0,
            tx_packets=0,
            rx_packets=0,
            tx_retries=0,
            capability_flags=["HT", "WNM"],
        )
    assert conn.state == "ESTABLISHED" and type(conn.state) is str
    assert record.record_type == "CAA" and type(record.record_type) is str
    assert qoe.protocol == "http/1.0" and type(qoe.protocol) is str
    assert user.eap_methods == ["PEAP-MSCHAPv2", "EAP-FAST"]
    assert acct.record_type == "Start" and type(acct.record_type) is str
    assert acct.terminate_cause == "Vendor-Cause" and type(acct.terminate_cause) is str
    assert flow.category == "gaming" and type(flow.category) is str
    assert flow_unknown.category == "vendor-category"
    assert station.capability_flags == ["HT", "WNM"]
    assert all(type(word) is str for word in station.capability_flags + user.eap_methods)
