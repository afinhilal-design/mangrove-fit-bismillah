from .schemas import values

def recommend(zone, screening):
    v = values(zone)
    status = screening['status']
    if status=='EXCLUDED':
        return {'action':'Tidak direkomendasikan untuk penanaman','focus':'Periksa batas ekologis/legal dan lindungi ekosistem eksisting.','next_steps':['Dokumentasikan alasan pengecualian bersama pengelola.','Jangan mengubah ekosistem nonhabitat menjadi area tanam mangrove.']}
    if v.get('tidal_connectivity')=='terganggu':
        focus = 'Kaji pemulihan hidrologi'
        steps = ['Survei aliran pasang surut dan sumber hambatan.','Tinjau opsi bersama ahli serta pengelola; kajian ini bukan perintah membuka tanggul.']
    elif v.get('wave_exposure')=='tinggi' or (v.get('shoreline_change_m_y') is not None and v['shoreline_change_m_y']<0):
        focus = 'Kaji dinamika pantai / tunda tanam'
        steps = ['Verifikasi abrasi, periode data, dan kestabilan sedimen.','Tinjau paparan gelombang sebelum menyusun intervensi.']
    elif zone['landcover_type']=='mangrove':
        focus = 'Lindungi dan pantau'
        steps = ['Periksa kesehatan dan tekanan pada mangrove eksisting.','Pantau regenerasi; tidak perlu penanaman ulang otomatis.']
    elif v.get('natural_recruitment')=='ada' and v.get('propagule_supply')=='cukup':
        focus = 'Fasilitasi regenerasi alami'
        steps = ['Pantau rekrutmen alami dan gangguan setempat.','Pertahankan konektivitas hidrologi setelah telaah ahli.']
    elif v.get('propagule_supply')=='terbatas':
        focus = 'Pertimbangkan penanaman terbatas'
        steps = ['Verifikasi substrat, spesies lokal, musim, dan kebutuhan penanaman.','Rancang uji terbatas hanya setelah peninjauan dan izin setempat.']
    else:
        focus = 'Kaji regenerasi dan kondisi habitat'
        steps = ['Survei penyebab belum munculnya regenerasi.','Evaluasi kondisi ekologis bersama ahli sebelum memilih strategi.']
    if status=='NEEDS_REVIEW':
        return {'action':'Wajib verifikasi lapangan','focus':focus+' (arah kajian sementara)','next_steps':['Lengkapi data inti dan verifikasi status legal terlebih dahulu.']+steps}
    return {'action':focus,'focus':'Opsi awal untuk ditinjau ahli; bukan izin pelaksanaan.','next_steps':steps}
