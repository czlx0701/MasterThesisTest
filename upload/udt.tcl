source base.tcl
set server_num [setup_network]

Agent/UDT set mtu_ 1500
Agent/UDT set max_flow_window_ 32768

set udt_list [$ns create-connection-list UDT $client UDT $server($target_server) 0]
set udtc [lindex $udt_list 0]
set udts [lindex $udt_list 1]
$udtc set class_ $target_server
$udts set class_ 0
$ns at 0 "$udtc sendmsg $fileSize DAT_EOF"

$udtc proc done_data {} {
    $self close
    [finish]
}
$ns run
