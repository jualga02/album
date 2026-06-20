import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Updateprofile } from './updateprofile';

describe('Updateprofile', () => {
  let component: Updateprofile;
  let fixture: ComponentFixture<Updateprofile>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Updateprofile],
    }).compileComponents();

    fixture = TestBed.createComponent(Updateprofile);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
