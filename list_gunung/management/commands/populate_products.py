import csv
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
# Pastikan impor model sudah benar
from list_gunung.models import Mountain  

class Command(BaseCommand):
    """
    Management command untuk mem-populate data gunung dari file CSV.
    """
    help = 'Populates the Mountain model from a given CSV file located in static/csv/gunung_data.csv'

    def handle(self, *args, **options):
        # 1. Tentukan path ke file CSV
        # Kita gunakan settings.BASE_DIR untuk mendapatkan root project
        csv_file_path = settings.BASE_DIR / 'static' / 'csv' / 'gunung_data.csv' 

        # 2. Validasi apakah file ada
        if not csv_file_path.exists():
            raise CommandError(f"File CSV tidak ditemukan di: {csv_file_path}")
        
        self.stdout.write(self.style.HTTP_INFO(f"Memulai populasi data dari {csv_file_path}..."))

        created_count = 0
        updated_count = 0

        # 3. Buka dan baca file CSV
        try:
            with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
                # Gunakan DictReader agar bisa mengakses kolom via nama headernya
                reader = csv.DictReader(file)

                for row in reader:
                    try:
                        # 4. Ambil data dari baris CSV dan konversi tipe data
                        # Sesuaikan nama kolom CSV dengan yang digunakan di bawah ini
                        name = row['name']
                        url = row['url']
                        # Konversi string ke integer untuk height_mdpl
                        height_mdpl = int(row['height_mdpl']) 
                        province = row['province']
                        # Gunakan .get() untuk kolom opsional
                        image_url = row.get('image_url', '') 
                        description = row.get('description', '') 

                        # 5. Gunakan update_or_create (Metode paling aman)
                        # Kita gunakan 'name' sebagai kunci unik untuk mencari data.
                        mountain, created = Mountain.objects.update_or_create(
                            # Kriteria pencarian/pembaruan (unique field)
                            name=name,
                            # Nilai yang akan dibuat atau diperbarui
                            defaults={
                                'url': url,
                                'height_mdpl': height_mdpl,
                                'province': province,
                                'image_url': image_url,
                                'description': description,
                            }
                        )

                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

                    except KeyError as e:
                        # Error jika nama kolom di CSV salah
                        self.stderr.write(self.style.ERROR(f"Kolom CSV tidak ditemukan: {e}. Baris: {row}"))
                    except ValueError as e:
                        # Error jika konversi 'height_mdpl' ke int gagal
                        self.stderr.write(self.style.ERROR(f"Data tidak valid (cth: height_mdpl): {e}. Baris: {row}"))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Error pada baris {row}: {e}"))

        except FileNotFoundError:
            raise CommandError(f"File CSV tidak ditemukan di: {csv_file_path}")
        except Exception as e:
            raise CommandError(f"Terjadi error saat memproses file: {e}")

        # 6. Beri laporan hasil
        self.stdout.write(self.style.SUCCESS(
            f"Proses selesai. Berhasil membuat: {created_count} gunung. Berhasil update: {updated_count} gunung."
        ))