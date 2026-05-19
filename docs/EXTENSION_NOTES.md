# Extension Notes

Proyek ini dikembangkan sebagai ekstensi dan kustomisasi dari repository demo distributed system:

https://github.com/goshlive/dist-system

Repository demo digunakan sebagai acuan konsep untuk messaging, RPC, service communication, dan distributed system. Proyek ini tidak hanya menyalin demo, tetapi mengembangkan studi kasus baru dengan domain Helpdesk Ticketing System.

## Bentuk Ekstensi

Pengembangan yang dilakukan meliputi:

1. Menambahkan studi kasus Helpdesk Ticketing System.
2. Menambahkan REST API menggunakan FastAPI.
3. Menambahkan dua instance Ticket Service.
4. Menambahkan Nginx sebagai API Load Balancer.
5. Menambahkan User Service berbasis gRPC.
6. Menambahkan RabbitMQ untuk asynchronous workflow.
7. Menambahkan Assignment Service sebagai worker.
8. Menambahkan Notification Service sebagai worker.
9. Menambahkan PostgreSQL sebagai persistent storage.
10. Menambahkan Hirschberg-Sinclair Leader Election Service.
11. Menambahkan GUI dashboard berbasis HTML, CSS, dan JavaScript.
12. Menambahkan Docker Compose untuk menjalankan seluruh service.

## Perbedaan dengan Demo Awal

Demo awal hanya menjadi dasar pemahaman konsep. Proyek ini memperluas konsep tersebut menjadi sistem terintegrasi yang memiliki alur bisnis lengkap.

Alur utama sistem:

1. User membuat tiket dari GUI.
2. Request masuk melalui Nginx Load Balancer.
3. Ticket Service memvalidasi user melalui gRPC ke User Service.
4. Ticket Service menyimpan tiket ke PostgreSQL.
5. Ticket Service mengirim event ticket_created ke RabbitMQ.
6. Assignment Service membaca event dan mengambil leader aktif.
7. Leader aktif digunakan sebagai koordinator assignment.
8. Assignment Service menyimpan hasil assignment.
9. Assignment Service mengirim event ticket_assigned.
10. Notification Service membuat notifikasi untuk user dan admin.

## Alasan Pemilihan Studi Kasus

Helpdesk Ticketing System dipilih karena alurnya jelas untuk membuktikan distributed system. Sistem ini membutuhkan REST API, komunikasi antar-service, message broker, database, leader election, dan GUI.

## Alasan Pemilihan Hirschberg-Sinclair

Hirschberg-Sinclair dipilih karena memiliki bobot tertinggi pada rubrik leader election. Algoritma ini digunakan untuk memilih leader dalam topologi ring. Pada proyek ini, leader digunakan sebagai koordinator assignment tiket.

## Bukti Kustomisasi

Kustomisasi utama terlihat pada:

- Domain aplikasi baru.
- Integrasi service yang lebih kompleks.
- Penggunaan gRPC berbasis stub.
- Workflow asynchronous berbasis RabbitMQ.
- Simulasi leader failure.
- Integrasi leader aktif ke proses assignment tiket.
- Dashboard GUI untuk demo sistem.
