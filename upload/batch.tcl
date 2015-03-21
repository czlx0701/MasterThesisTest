source base.tcl
set server_num [setup_network]

Class BatchSendManager

BatchSendManager instproc init {file_size conn_num} {
	$self instvar left_ idle_
    set left_ $file_size
    set working_ $conn_num
}

BatchSendManager instproc check_working {} {
    $self instvar working_
    if {$working_ < 1} {
        [finish]
    }
}

BatchSendManager instproc on_conn_ready {expect_send} {
    $self instvar left_ working_
    if {$left_ >= $expect_send} {
        set sent $expect_send
    } else {
        if {$left_ < 1} {
            incr working_ -1
            $self check_working
            return 0
        } else {
            set sent $left_
        }
    }
    set left_ [expr $left_ - $sent]
    return $sent
}

Class Application/ClientApp -superclass Application

Application/ClientApp instproc on_start {} {
	$self instvar time_ min_time_ time_thre_ last_size_ bandwidth_
	$self instvar alpha_ beta_
    set time_ -1
    set min_time_ 0.25
    set time_thre_ 2
    # 1M
    set last_size_ [expr 1024 * 1024]
    set bandwidth_ -1
    set alpha_ 0.7
    set beta_  0.7
    $self ready
}

Application/ClientApp instproc calc_size {} {
    $self instvar time_ min_time_ time_thre_ last_size_ bandwidth_
	$self instvar alpha_ beta_
    if {$time_ <= 0} {
        return
    }
    if {$time_ <= $min_time_} {
        set now_bandwidth [expr $last_size_ / $min_time_]
    } else {
        set now_bandwidth [expr $last_size_ / $time_]
    }
    if  {$bandwidth_ < 0} {
        set bandwidth_ $now_bandwidth
    } else {
        if {$time_ > $time_thre_} {
            set bandwidth_ [expr $alpha_ * $now_bandwidth + (1 - $alpha_) * $bandwidth_]
        } else {
            set bandwidth_ [expr $beta_ * $now_bandwidth + (1 - $beta_) * $bandwidth_]
        }
    }
    set last_size_ [expr $bandwidth_ * $time_thre_]
}

Application/ClientApp instproc ready {} {
    $self instvar last_send_ last_size_ manager_
    global ns

    set last_size_ [$manager_ on_conn_ready $last_size_]
    if {$last_size_ > 0} {
        set last_send_ [$ns now]
        # POST /upload/chunk?upload_id=0123456789abcdef0123456789abcdef&offset=123456 HTTP/1.1
        # Host: www.example.com
        # Content-Type:application/octet-stream
        # Content-Length: 12345
        # 
        # Data
        #
        [$self agent] sendmsg [expr $last_size_ + 100] "DAT_EOF"
    }
}

Application/ClientApp instproc recv {count} {
    global ns
    $self instvar last_send_ time_
    # got response from server
    set now [$ns now];
    set time_ [expr $now - $last_send_];
    $self calc_size
    $self ready
}

Class Application/ServerApp -superclass Application

Application/ServerApp instproc send_ack {} {
    # HTTP/1.1 200 OK
    # Content-Type: application/json; charset=utf-8
    # Content-Length: 1xx
    #
    # {"result": "OK"}
    $self send 100
}

Application/ServerApp instproc on_start {} {
    [$self agent] listen
}

proc create_app {ns manager tcpc tcps} {
    set appc [new Application/ClientApp]
    set apps [new Application/ServerApp]
    $tcpc proc done_data {} {
        $self instvar server
        $server send_ack
    }
    $tcpc set server $apps;
    $appc set manager_ $manager;
    $appc attach-agent $tcpc;
    $apps attach-agent $tcps;
    $ns at 0 "$apps start"
    $ns at 0 "$appc start"
    return {$appc $apps}
}

set manager [new BatchSendManager $fileSize $server_num]
for {set i 1} {$i <= $server_num} {incr i} {
    set tcp_list [$ns create-connection-list TCP/FullTcp $client TCP/FullTcp $server($i) 0]
    set tcpc($i) [lindex $tcp_list 0]
    set tcps($i) [lindex $tcp_list 1]
    $tcpc($i) set class_ $i
    $tcps($i) set class_ 0
    set app($i) [create_app $ns $manager $tcpc($i) $tcps($i)]
}
$ns run
