import os
import piexif
import pickle

def import_GPS_data():
    with open("C:/Users/geral/Documents/GitHub/Cam-GPS/GPGGA_list.pkl", "rb") as file:
        GPGGA_list = pickle.load(file)
    return GPGGA_list

# Convert raw GPS data to proper format, in particular time and coordindates (DDM to DMS)
# Sample DDM: ['202430.00 6109.48868 N 14951.26991 W 32.1 M']
def convert_GPS_data(GPGGA_list, date):   
    DMS_list = []

    for fix in GPGGA_list:        
        if len(fix) > 15: # This only attaches GPS data if it exists (if GPS module had no fix it will be 15 characters for just the time)
            fix = date + ' ' + fix
            fix = fix.split(' ')
            # Conversions
            # Time is not populated in this EXIF program, but I have this in here in case I want to add it in later
            time = fix[1][0] + fix[1][1] + ':' + fix[1][2] + fix[1][3] + ':' + fix[1][4] + fix[1][5]

            lat_DDMMm5 = fix[2]                         # Ublox-7 outputs lat in DDMMmmmmm
            lat_DDMMm5 = lat_DDMMm5.split('.')
            long_DDDMMm5 = fix[4]
            long_DDDMMm5 = long_DDDMMm5.split('.')       # Ublox-7 outputs long in DDDMMmmmmm

            lat_deg = int(lat_DDMMm5[0][0] + lat_DDMMm5[0][1])
            lat_min = int(lat_DDMMm5[0][2] + lat_DDMMm5[0][3])
            lat_sec = round(float(lat_DDMMm5[1])*60/100000, 3)

            long_deg = int(long_DDDMMm5[0][0] + long_DDDMMm5[0][1] + long_DDDMMm5[0][2])
            long_min = int(long_DDDMMm5[0][3] + long_DDDMMm5[0][4])
            long_sec = round(float(long_DDDMMm5[1])*60/100000, 3)

            # Put in format for EXIF
            fix[1] = time
            fix[2] = lat_deg
            fix.insert(3, lat_min)
            fix.insert(4, lat_sec)
            fix[6] = long_deg
            fix.insert(7, long_min)
            fix.insert(8, long_sec)
            # Altitude
            fix[-2] = round(float(fix[-2]))
            del fix[-1]        

        else:       
            fix = fix.split(' ')
            # The fix in this case is just time with blank spots for GPS. 
            #E.g., ['014917.00', '', '', '', '', '', '']
            
            time = fix[0][0] + fix[0][1] + ':' + fix[0][2] + fix[0][3] + ':' + fix[0][4] + fix[0][5]
            fix = [date, time]

        DMS_list.append(fix)

    return DMS_list


def insert_EXIF(DMS_list):
    # Sample DMS_list:
    # [['2024:01:01', '13:00:00', 14, 35, 59.892, 'S', 120, 58, 53.184, 'E', '100'], 
    #  ['2024:01:01', '14:00:00', 48, 51, 26.064, 'N', 2, 21, 18.972, 'E', '200'], 
    #  ['2024:01:01', '15:00:00', 23, 33, 40.572, 'S', 46, 40, 10.236, 'W', '300']]
    # If GPS coords missing, it will be ['2024:08:13', '02:03:56']
    
    # Make list of photo files
    input_folder = 'C:/Users/geral/Documents/GitHub/Cam-GPS/Photos'
    img_files_list = os.listdir(input_folder)

    root = 'C:/Users/geral/Documents/GitHub/Cam-GPS/Photos/'

    files_list = []

    for file in img_files_list:
        path = root + file
        files_list.append(path)

    # Cycle through location/time data from GPS (DMS_list) then assign to EXIF variables
    for x in range(len(DMS_list)):
        if len(DMS_list[x]) > 2:    # Skips over list elements without GPS fix
            # date_taken = DMS_list[x][0] + ' ' + DMS_list[x][1]

            lat_hemi = DMS_list[x][5]
            lat_deg = DMS_list[x][2] 
            lat_min = DMS_list[x][3]
            lat_sec = int(DMS_list[x][4]*1000)

            long_hemi = DMS_list[x][9]
            long_deg = DMS_list[x][6] 
            long_min = DMS_list[x][7]
            long_sec = int(DMS_list[x][8]*1000)

            alt = DMS_list[x][10]*10

            # Load EXIF then write to it
            meta = piexif.load(files_list[x])
            
            # if date_taken:
            #     meta["Exif"][36867] = date_taken
            if lat_hemi != None and lat_deg != None and lat_min != None and lat_sec != None:
                meta["GPS"][1] = lat_hemi
                meta["GPS"][2] = ((lat_deg,1), (lat_min,1), (lat_sec, 1000))
            if long_hemi != None and long_deg != None and long_min != None and long_sec != None:
                meta['GPS'][3] = long_hemi
                meta["GPS"][4] = ((long_deg,1), (long_min,1), (long_sec, 1000))
            if alt != None:
                meta["GPS"][6] = (alt, 10)

            exif_bytes = piexif.dump(meta)

            piexif.insert(exif_bytes, files_list[x])
    

def main(): 
    date = '2024:08:13'          # Manually edit this because it's not in the GPGGA lines

    GPGGA_list = import_GPS_data() 

    DMS_list = convert_GPS_data(GPGGA_list, date)

    insert_EXIF(DMS_list)

if __name__ == '__main__':
    main()

























# References
# 1. https://blog.matthewgove.com/2022/05/13/how-to-bulk-edit-your-photos-exif-data-with-10-lines-of-python/