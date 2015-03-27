# Measure the end to end delay by the trace file

BEGIN{
	# program initialize
	highest_packet_id = 0;
}

{
	# awk会自动循环执行这个{}
	action = $1;
	time = $2;
	from = $3;
	to = $4;
	type = $5;
	pktsize = $6;
	flow_id = $8;
	src = $9;
	dst = $10;
	seq_no = $11;
	packet_id = $12;

	# Record the current max packet ID
	if ( packet_id > highest_packet_id )
		highest_packet_id = packet_id;

	# Record the tx time of packet
	if ( start_time[packet_id] == 0 )
		start_time[packet_id] = time;

	# Record CBR flow_id=2 rx time
	# 这里既要判断flow=2，没有drop，还要判断recv
	# drop是必须的，因为有可能1-2 recv，2-3 drop了
	# CBR 路径是1-2-3，整条路径上都有可能drop
	if ( flow_id == 1 && action != "d" )
	{
		if (action == "r")
		{
			end_time[packet_id] = time;
		}
	}
	else
		end_time[packet_id] = -1;
}

END {
# When read over, start to calculate
	for ( packet_id=0; packet_id<=highest_packet_id; packet_id++ )
	{
		start = start_time[packet_id];
		end = end_time[packet_id];
		duration = start-end;
		if (start<end)
			printf("%f %f\n", start, duration);
	}
}

