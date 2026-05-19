# Presentation Script

Durasi maksimal presentasi adalah 10 menit.

## 0:00 - 1:00 Pembukaan

Selamat pagi. Kami akan mempresentasikan proyek UAS Sistem Terdistribusi berjudul Distributed Helpdesk Ticketing System.

Proyek ini menggunakan studi kasus helpdesk ticketing. User dapat membuat tiket keluhan melalui dashboard. Sistem kemudian memvalidasi user, menyimpan tiket, memproses assignment admin, membuat notifikasi, dan memilih leader aktif menggunakan Hirschberg-Sinclair Leader Election.

## 1:00 - 2:00 Arsitektur Sistem

Sistem ini terdiri dari beberapa service:

1. Frontend GUI.
2. Nginx Load Balancer.
3. Ticket Service 1 dan Ticket Service 2.
4. User Service berbasis gRPC.
5. Assignment Service.
6. Notification Service.
7. Leader Election Service.
8. RabbitMQ.
9. PostgreSQL.

Setiap service memiliki tanggung jawab berbeda agar konsep distributed system terlihat jelas.

## 2:00 - 3:00 Demo Docker dan GUI

Kami menjalankan semua service menggunakan Docker Compose.

Command yang digunakan:

```bash
docker compose up --build -d
docker ps
```
