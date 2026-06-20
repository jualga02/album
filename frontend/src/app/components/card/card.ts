import { DatePipe } from '@angular/common';
import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';

@Component({
  selector: 'app-card',
  imports: [DatePipe],
  templateUrl: './card.html',
  styleUrl: './card.css',
})
export class Card implements OnInit{
  @Input() id: number = 0;
  @Input() link: string = '';
  @Input() comment: string = '';
  @Input() name: string = '';
  @Input() user:number= 0;
  @Input() title: string = '';
  @Input() tag: string = '';
  @Input() shot_date: Date = new Date();
  @Input() video: boolean = false;

  @Output() watch = new EventEmitter<number>();
  @Output() edit = new EventEmitter<number>();
  @Output() delete = new EventEmitter<number>();

  public owner: boolean = false;
  public videoLogo: string = 'logo_video.png';

  public onClickWatch():void {
    this.watch.emit(this.id);
  }

  public onClickEdit():void {
    this.edit.emit(this.id);
  }

  public onClickDelete():void {
    this.delete.emit(this.id);
  }

  public ngOnInit(): void {
    if(String(this.user) == window.sessionStorage.getItem('user_id')){
      this.owner = true;
    } else {
      this.owner = false;
    }
  }
}
