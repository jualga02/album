import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Photodelete } from './photodelete';

describe('Photodelete', () => {
  let component: Photodelete;
  let fixture: ComponentFixture<Photodelete>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Photodelete],
    }).compileComponents();

    fixture = TestBed.createComponent(Photodelete);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
