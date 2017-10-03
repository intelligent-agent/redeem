var path = require('path');
var gulp = require('gulp');
var shell = require('gulp-shell');
var less = require('gulp-less');
var rename = require("gulp-rename");
var plumber = require('gulp-plumber');

// for modifying the theme, first `git clone` then `pip install -e .`
var theme_dir = '../../sphinxtheme-replicape/sphinxtheme_replicape/';

gulp.task('sphinx_to_html', shell.task('make html'));

gulp.task('less_to_css', function () {
  return gulp.src(theme_dir + '**/styles.less')
      .pipe(plumber())
      .pipe(less())
      .pipe(rename({
          dirname: "",
          extname: ".css"
      }))
    .pipe(gulp.dest(theme_dir + 'static/css/'));
});

gulp.task('build_and_watch', ['sphinx_to_html'],function() {
   gulp.watch([
       './**/*.rst',
       '../redeem/**/*.py'
   ], ['sphinx_to_html']);
});

gulp.task('develop', ['less_to_css', 'sphinx_to_html'],function() {
   gulp.watch([
       './**/*.rst',
       '../redeem/**/*.py',
       './**/*.py',
       theme_dir+'**/*.css',
       theme_dir+'*.html',
       theme_dir+'**/*.less',
       theme_dir+'**/*.js'
   ], ['less_to_css','sphinx_to_html']);
});

gulp.task('build-versions',
    shell.task(
        'sphinx-versioning build docs docs/_build/html',
        { 'cwd': path.join(process.cwd(), '../') }
        )
);

gulp.task('default', [ 'build_and_watch' ]);
