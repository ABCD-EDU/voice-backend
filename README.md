# Speech Separation Backend
To run the server on development mode, use the following commands on the root folder:

### Job API
`python -m uvicorn job.main:app --port 8000 --host 0.0.0.0 --reload`

### Models API
`python -m uvicorn models.main:app --port 8001 --host 0.0.0.0 --reload`

> Access the server by going to `127.0.0.1:8000` and `127.0.0.1:8001` <br/>

## How to Port Forward WSL2 to other Devices

1. Open PowerShell as Admin
2. Run the following script to expose your local IPv4 to other devices
```

$remoteport = bash.exe -c "ifconfig eth0 | grep 'inet '"
$found = $remoteport -match '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}';

if( $found ){
  $remoteport = $matches[0];
} else{
  echo "The Script Exited, the ip address of WSL 2 cannot be found";
  exit;
}

#[Ports]

#All the ports you want to forward separated by coma
# 800x - FastAPI servers: Models and Job
# 3306 - Database
# 9092 - Kafka
# 900x - MinIO
$ports=@(80,443,10000,3000,5000,8000,8001,8002,3306,9092,9000,9001,9002);

#[Static ip]
#You can change the addr to your ip config to listen to a specific address
$addr='0.0.0.0';
$ports_a = $ports -join ",";


#Remove Firewall Exception Rules
iex "Remove-NetFireWallRule -DisplayName 'WSL 2 Firewall Unlock' ";

#adding Exception Rules for inbound and outbound Rules
iex "New-NetFireWallRule -DisplayName 'WSL 2 Firewall Unlock' -Direction Outbound -LocalPort $ports_a -Action Allow -Protocol TCP";
iex "New-NetFireWallRule -DisplayName 'WSL 2 Firewall Unlock' -Direction Inbound -LocalPort $ports_a -Action Allow -Protocol TCP";

for( $i = 0; $i -lt $ports.length; $i++ ){
  $port = $ports[$i];
  iex "netsh interface portproxy delete v4tov4 listenport=$port listenaddress=$addr";
  iex "netsh interface portproxy add v4tov4 listenport=$port listenaddress=$addr connectport=$port connectaddress=$remoteport";
}
```

> Reference: https://github.com/microsoft/WSL/issues/4150
