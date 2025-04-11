Installing Arkitekt on GROGU
```
sudo su arkitekt
mkdir peeling_realtime
cd peeling_realtime/
python3 -m venv arkitekt2
. arkitekt2/bin/activate
pip install "arkitekt-next[all,blok]==0.8.83"
blok build arkitekt .
```

```
ls
  arkitekt2  __blok__.yml  certs  configs  data  docker-compose.yml
docker compose pull
docker compose up
```

If old stuff form older installations is left, you need to do:
```
docker compose down
docker compose pull
```
Beware - deletes the installed stuff!

to check the logs of a particular arkitekt service for example `lok`
```
docker compose logs lok
```


If I want to reproduce a specific version of all arkitekt services manually, I would use:
```
block build arkitekt there --fluss-dev --mikro-dev --lok-dev .........
```
This would pull the latest versions from github, but as long as they stay on disk and the dependencies don't change, I can go and manually checkout an earlier commit for each service, and then I'll get a frozen earlier version of arkitekt.
A working list of commits for all services:
```
kabinet-server=[34bcec2](https://github.com/arkitektio/kabinet-server/commit/34bcec2abfd3649bf1d58d019b8a7b8811e26d6d)
mikro-server-next=[42250bc](https://github.com/arkitektio/mikro-server-next/commit/42250bceb59a20019cf40a4da344c7c102678534)
lok-server-next=[48cea6b](https://github.com/arkitektio/lok-server-next/commit/48cea6b13909adf84c21cdce9227fc8eced8293f)
rekuest-server-next=[e66584f](https://github.com/arkitektio/rekuest-server-next/commit/e66584f6d4b0979171836506f1c6223759e23738)
fluss-server-next=[acf9d3f](https://github.com/arkitektio/fluss-server-next/commit/acf9d3f9821b59d411990dae696f79e0b0deddba)
```
