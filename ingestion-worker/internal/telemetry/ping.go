package telemetry

// GPSPing intentionally uses the legacy protobuf tags supported by
// github.com/golang/protobuf/proto. It keeps this MVP runnable without
// committing generated code; once protoc is available this can be replaced by
// the generated type from proto/gps_ping.proto without changing the wire format.
type GPSPing struct {
	BusID            string  `protobuf:"bytes,1,opt,name=bus_id,json=busId,proto3" json:"bus_id,omitempty"`
	RouteID          string  `protobuf:"bytes,2,opt,name=route_id,json=routeId,proto3" json:"route_id,omitempty"`
	Latitude         float64 `protobuf:"fixed64,3,opt,name=latitude,proto3" json:"latitude,omitempty"`
	Longitude        float64 `protobuf:"fixed64,4,opt,name=longitude,proto3" json:"longitude,omitempty"`
	SpeedMPS         float32 `protobuf:"fixed32,5,opt,name=speed_mps,json=speedMps,proto3" json:"speed_mps,omitempty"`
	HeadingDegrees   float32 `protobuf:"fixed32,6,opt,name=heading_degrees,json=headingDegrees,proto3" json:"heading_degrees,omitempty"`
	CapturedAtUnixMS int64   `protobuf:"varint,7,opt,name=captured_at_unix_ms,json=capturedAtUnixMs,proto3" json:"captured_at_unix_ms,omitempty"`
}

func (p *GPSPing) Reset()         { *p = GPSPing{} }
func (p *GPSPing) String() string { return p.BusID }
func (*GPSPing) ProtoMessage()    {}
