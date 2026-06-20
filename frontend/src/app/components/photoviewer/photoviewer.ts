import { Component, Input, HostListener, input, signal, computed, ElementRef, ViewChild } from '@angular/core';
import { Photoresponse } from '../../models/photoresponse.interface';

@Component({
  selector: 'app-photoviewer',
  standalone: true,
  imports: [],
  templateUrl: './photoviewer.html',
  styleUrl: './photoviewer.css',
})
export class Photoviewer {

 @Input() id: number = 0;
  images = input<Photoresponse[]>([]);
  
  // Referencia al elemento de video para controlarlo
  @ViewChild('videoPlayer') videoPlayer!: ElementRef<HTMLVideoElement>;

  // Tipo de medio actual ('photo' o 'video')
  currentMediaType = signal<'photo' | 'video'>('photo');

  // Filtramos según el tipo de medio que se abrió inicialmente
  filteredMedia = computed(() => {
    const isVideo = this.currentMediaType() === 'video';
    return this.images().filter(img => img.video === isVideo);
  });

  isOpen = signal(false);
  currentIndex = signal(0);
  zoom = signal(1);

  currentMedia = computed(() => {
    const media = this.filteredMedia();
    if (media.length === 0) return null;
    return media[this.currentIndex()];
  });

  open(originalIndex: number): void {
    const allMedia = this.images();
    if (originalIndex >= allMedia.length) return;

    // 1. Detectar si el elemento clicado es video o foto
    const clickedItem = allMedia[originalIndex];
    this.currentMediaType.set(clickedItem.video ? 'video' : 'photo');

    const filtered = this.filteredMedia();
    if (filtered.length === 0) {
      this.isOpen.set(false);
      return;
    }

    // 2. Mapear al índice del array filtrado
    let newIndex = filtered.findIndex(img => img === clickedItem);
    if (newIndex === -1) newIndex = 0;

    this.currentIndex.set(newIndex);
    this.zoom.set(1);
    this.isOpen.set(true);
    document.body.style.overflow = 'hidden';
  }

  close(): void {
    this.pauseVideo(); // Importante: pausar al cerrar
    this.isOpen.set(false);
    this.zoom.set(1);
    document.body.style.overflow = 'auto';
  }

  next(): void {
    this.pauseVideo(); // Pausar antes de cambiar
    const media = this.filteredMedia();
    if (this.currentIndex() < media.length - 1) {
      this.currentIndex.update(v => v + 1);
      this.zoom.set(1);
    }
  }

  prev(): void {
    this.pauseVideo(); // Pausar antes de cambiar
    if (this.currentIndex() > 0) {
      this.currentIndex.update(v => v - 1);
      this.zoom.set(1);
    }
  }

  private pauseVideo(): void {
    if (this.currentMediaType() === 'video' && this.videoPlayer?.nativeElement) {
      this.videoPlayer.nativeElement.pause();
    }
  }

  zoomIn(): void {
    if (this.currentMediaType() === 'photo') {
      this.zoom.update(v => v + 0.2);
    }
  }

  zoomOut(): void {
    if (this.currentMediaType() === 'photo' && this.zoom() > 0.4) {
      this.zoom.update(v => v - 0.2);
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.isOpen()) this.close();
  }

  @HostListener('document:keydown.arrowright')
  onRight(): void {
    if (this.isOpen()) this.next();
  }

  @HostListener('document:keydown.arrowleft')
  onLeft(): void {
    if (this.isOpen()) this.prev();
  }

  ngOnInit(): void {
    // Si quieres que se abra automáticamente al cargar el componente
    if (this.id >= 0) {
      this.open(this.id);
    }
  }
}