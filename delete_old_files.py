import os
import time
import glob

def delete_old_files(directory, hours=3):
    """Elimina i file più vecchi di un certo numero di ore."""
    current_time = time.time()
    cutoff_time = current_time - (hours * 3600)
    
    count = 0
    for file_path in glob.glob(f"{directory}/*"):
        if os.path.isfile(file_path):
            file_mod_time = os.path.getmtime(file_path)
            if file_mod_time < cutoff_time:
                print(f"Eliminando: {file_path} (modificato {(current_time - file_mod_time) / 3600:.2f} ore fa)")
                os.remove(file_path)
                count += 1
    
    return count

if __name__ == "__main__":
    if os.path.exists("logos"):
        count = delete_old_files("logos")
        print(f"Eliminati {count} file più vecchi di 3 ore dalla cartella logos")
    else:
        print("La cartella logos non esiste")
