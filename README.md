# Distributed Helpdesk Ticketing System

Proyek ini merupakan mini proyek UAS mata kuliah Sistem Terdistribusi. Sistem ini dikembangkan sebagai ekstensi dan kustomisasi dari repository demo distributed system yang diberikan dosen, yaitu `https://github.com/goshlive/dist-system`.

## Studi Kasus

Studi kasus yang digunakan adalah Helpdesk Ticketing System. User dapat membuat tiket keluhan melalui GUI. Sistem kemudian memvalidasi user melalui gRPC, menyimpan tiket ke database, mengirim event ke RabbitMQ, melakukan assignment tiket kepada admin, membuat notifikasi, dan menggunakan leader aktif dari proses Hirschberg-Sinclair Leader Election.

## Teknologi yang Digunakan

- Python
- FastAPI
- gRPC
- RabbitMQ
- PostgreSQL
- Nginx Load Balancer
- Docker Compose
- HTML, CSS, JavaScript
- Hirschberg-Sinclair Leader Election

## Arsitektur Service

Sistem terdiri dari beberapa service:

1. Frontend GUI
2. Nginx Load Balancer
3. Ticket Service 1
4. Ticket Service 2
5. User Service gRPC
6. Assignment Service
7. Notification Service
8. Leader Election Service
9. RabbitMQ
10. PostgreSQL

## Fitur Utama

- Membuat tiket melalui GUI
- REST API untuk ticketing
- Validasi user melalui gRPC
- Event asynchronous menggunakan RabbitMQ
- Assignment tiket otomatis ke admin
- Notifikasi otomatis untuk user dan admin
- Leader Election menggunakan Hirschberg-Sinclair
- Simulasi leader failure
- API Load Balancing menggunakan Nginx
- Deployment menggunakan Docker Compose

## Cara Menjalankan Project

Pastikan Docker Desktop sudah berjalan.

```bash
docker compose up --build -d
```

Cek container:

```bash
docker ps
```

Untuk menghentikan semua service:

```bash
docker compose down
```

## Akses Aplikasi

- Frontend GUI: http://localhost:3000
- API Gateway: http://localhost:8080
- Ticket Service 1: http://localhost:8001
- Ticket Service 2: http://localhost:8002
- Leader Election Service: http://localhost:9000
- RabbitMQ Management UI: http://localhost:15672

Login RabbitMQ:

```text
username: guest
password: guest
```

## Endpoint Utama

### Ticket Service

```text
GET    /health
POST   /tickets
GET    /tickets
GET    /tickets/{id}
PUT    /tickets/{id}/status
GET    /assignments
GET    /notifications
GET    /grpc/users/{user_id}
GET    /grpc/admins
```

### Leader Election Service

```text
GET    /health
GET    /nodes
GET    /leader
GET    /logs
POST   /election/start
POST   /nodes/{node_id}/fail
POST   /nodes/{node_id}/recover
```

## Alur Sistem

1. User membuat tiket melalui GUI.
2. Request masuk melalui Nginx Load Balancer.
3. Nginx meneruskan request ke Ticket Service 1 atau Ticket Service 2.
4. Ticket Service memvalidasi user melalui gRPC ke User Service.
5. Ticket Service menyimpan tiket ke PostgreSQL.
6. Ticket Service mengirim event `ticket_created` ke RabbitMQ.
7. Assignment Service membaca event dari RabbitMQ.
8. Assignment Service mengambil leader aktif dari Leader Election Service.
9. Assignment Service memilih admin dan menyimpan assignment.
10. Assignment Service mengirim event `ticket_assigned` ke RabbitMQ.
11. Notification Service membaca event dan membuat notifikasi.
12. GUI menampilkan tiket, assignment, notifikasi, dan leader aktif.

## Leader Election

Leader Election menggunakan algoritma Hirschberg-Sinclair dengan topologi ring.

Node yang digunakan:

```text
10, 20, 30, 40, 50
```

Pada kondisi awal, node dengan ID tertinggi, yaitu node 50, menjadi leader.

Jika node 50 dimatikan, sistem menjalankan election ulang dan memilih node 40 sebagai leader baru.

Leader aktif digunakan dalam proses assignment tiket. Nilai leader disimpan pada kolom `assigned_by_leader_id`.

## RabbitMQ Queue

| Queue                 | Producer           | Consumer             |
| --------------------- | ------------------ | -------------------- |
| ticket_created_queue  | Ticket Service     | Assignment Service   |
| ticket_assigned_queue | Assignment Service | Notification Service |
| ticket_closed_queue   | Ticket Service     | Notification Service |

## Skenario Demo

1. Jalankan semua container dengan Docker Compose.
2. Buka GUI di `http://localhost:3000`.
3. Tampilkan leader aktif.
4. Buat tiket baru melalui form.
5. Tampilkan tiket masuk ke daftar tiket.
6. Tampilkan assignment otomatis.
7. Tampilkan notifikasi otomatis.
8. Buka RabbitMQ Management UI untuk melihat queue.
9. Klik tombol Fail Node 50.
10. Jalankan election ulang.
11. Tampilkan leader berubah menjadi node 40.
12. Buat tiket baru.
13. Tampilkan assignment menggunakan leader ID 40.
14. Klik tombol Recover Node 50.
15. Jalankan election ulang.
16. Tampilkan leader kembali menjadi node 50.

## Bukti Requirement

| Requirement            | Implementasi                                                   |
| ---------------------- | -------------------------------------------------------------- |
| REST API               | FastAPI pada Ticket Service                                    |
| Service-to-service RPC | gRPC antara Ticket Service dan User Service                    |
| RabbitMQ               | Event `ticket_created`, `ticket_assigned`, dan `ticket_closed` |
| Persistent Storage     | PostgreSQL                                                     |
| Case Study             | Helpdesk Ticketing System                                      |
| Leader Election        | Hirschberg-Sinclair                                            |
| API Load Balancing     | Nginx ke dua instance Ticket Service                           |
| Docker                 | Docker Compose                                                 |
| GUI                    | Dashboard HTML, CSS, dan JavaScript                            |
| GitHub                 | Source code dipublish pada repository GitHub                   |

## Struktur Folder

```text
distributed-helpdesk-system/
├── assignment-service/
├── database/
├── docs/
├── frontend/
├── leader-election-service/
├── nginx/
├── notification-service/
├── ticket-service/
├── user-service/
├── docker-compose.yml
└── README.md
```

## Kesimpulan

Proyek ini membangun sistem helpdesk berbasis distributed service. Sistem tidak hanya menyediakan aplikasi ticketing, tetapi juga membuktikan konsep utama sistem terdistribusi, yaitu REST API, komunikasi antar-service, asynchronous messaging, persistent storage, leader election, load balancing, containerization, dan GUI.
