import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Photoviewer } from './photoviewer';

describe('Photoviewer', () => {
  let component: Photoviewer;
  let fixture: ComponentFixture<Photoviewer>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Photoviewer],
    }).compileComponents();

    fixture = TestBed.createComponent(Photoviewer);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
